/*
 * Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef CUDA_PLUGIN_H
#define CUDA_PLUGIN_H

#pragma once
#include <iostream>
#include <vector>
#include <map>

#include "paillier.h"
#include "base_plugin.h"
#include "local_plugin.h"
#include "endec.h"
#include "timer.h"

#define PRECISION 1e9


namespace nvflare {

class Context {
  private:
    size_t _total_bin_size = 0;
    size_t* _bin_length;
    int _map_it_offset = 0;

  public:
    explicit Context(
      size_t total_bin_size,
      size_t* bin_length
    ) {
      _total_bin_size = total_bin_size;
      _bin_length = bin_length;
    }

    void get_next_chunk(int& bid, int& start_idx, int& end_idx, int remaining_slots, int tuple_length = 2) {
      int remaining_item_slots = remaining_slots * tuple_length;
      start_idx = -1;
      end_idx = -1;

      for (auto i = _map_it_offset; i < _total_bin_size; ++i) {
          size_t bin_length = _bin_length[i];
          if (bin_length < tuple_length) {
              continue;
          }
          
          if (remaining_item_slots >= bin_length) {
              int tuples = bin_length / tuple_length;
              end_idx = bin_length - 1;
              start_idx = end_idx - tuples * tuple_length + 1;
              _bin_length[i] -= tuples * tuple_length;
              bid = i;
              _map_it_offset = i;
              break;
          } else {
              int tuples = remaining_slots;
              end_idx = bin_length - 1;
              start_idx = end_idx - tuples * tuple_length + 1;
              _bin_length[i] -= tuples * tuple_length;
              bid = i;
              break;
          }
      }
    }
};

// Define a structured header for the buffer
struct BufferHeader2 {
  bool has_key;
  size_t key_size;
  size_t rand_seed_size;
};

class CUDAPlugin: public LocalPlugin {
  private:
    PaillierCipher<bits>* paillier_cipher_ptr_ = nullptr;
    CgbnPair* encrypted_gh_pairs_ = nullptr;
    Endec* endec_ptr_ = nullptr;
    CgbnPair* bin_array_ = nullptr;
    size_t* bin_length_ = nullptr;
    size_t* bin_start_idx_ = nullptr;
    CgbnPair* d_cell_table = nullptr;
    CgbnPair* cell_table = nullptr;

    Timer overall_timer_;
    double total_agg_time_ = 0;
    double total_prepare_bin_time_ = 0;
    size_t cell_table_size = 0;

  public:
    explicit CUDAPlugin(std::vector<std::pair<std::string_view, std::string_view> > const &args): LocalPlugin(args) {
      bool fix_seed = get_bool(args, "fix_seed");
      paillier_cipher_ptr_ = new PaillierCipher<bits>(bits/2, fix_seed, debug_);
      encrypted_gh_pairs_ = nullptr;
      cell_table = nullptr;
      d_cell_table = nullptr;
      bin_array_ = nullptr;
      bin_length_ = nullptr;
      bin_start_idx_ = nullptr;
    }

    ~CUDAPlugin() {
      delete paillier_cipher_ptr_;
      if (endec_ptr_ != nullptr) {
        delete endec_ptr_;
        endec_ptr_ = nullptr;
      }
      if (cell_table) {
        free(cell_table);
        cell_table = nullptr;
      }
      if (d_cell_table) {
        cudaFree(d_cell_table);
        d_cell_table = nullptr;
      }
      if (print_timing_) {
        std::cout << overall_timer_.now() << ": total prepare bin_xxx Time "<< total_prepare_bin_time_ <<" US"<<std::endl;
        std::cout << overall_timer_.now() << ": total_agg_time_ Time "<< total_agg_time_ <<" US"<<std::endl;
      }
    }

    void setGHPairs() {
      if (debug_) std::cout << "setGHPairs is called" << std::endl;
      const std::uint8_t* pointer = encrypted_gh_.data();

      // Retrieve header
      BufferHeader2 header;
      std::memcpy(&header, pointer, sizeof(BufferHeader2));
      pointer += sizeof(BufferHeader2);

      // Get key and n (if present)
      cgbn_mem_t<bits>* key_ptr;
      if (header.has_key) {
        mpz_t n;
        mpz_init(n);
        key_ptr = (cgbn_mem_t<bits>* )malloc(header.key_size);
        if (!key_ptr) {
          std::cout << "bad alloc with key_ptr" << std::endl;
          throw std::bad_alloc();
        }
        memcpy(key_ptr, pointer, header.key_size);
        store2Gmp(n, key_ptr);
        pointer += header.key_size;

        if (header.rand_seed_size != sizeof(uint64_t)) {
          free(key_ptr);
          mpz_clear(n);
          std::cout << "rand_seed_size " << header.rand_seed_size << " is wrong " << std::endl;
          throw std::runtime_error("Invalid random seed size");
        }
        uint64_t rand_seed;
        memcpy(&rand_seed, pointer, header.rand_seed_size);
        pointer += header.rand_seed_size;

        if (!paillier_cipher_ptr_->has_pub_key) {
          paillier_cipher_ptr_->set_pub_key(n, rand_seed);
        }
        mpz_clear(n);
        free(key_ptr);
      }

      // Access payload
      size_t remaining_size = encrypted_gh_.size() - (pointer - encrypted_gh_.data());
      if (remaining_size % sizeof(CgbnPair) != 0) {
        // the data isn't a perfect multiple of CgbnPair size
        throw std::runtime_error("The remaining data is not a multiple of sizeof(CgbnPair).");
      }
      if (debug_) std::cout << "num of gh pair is " << remaining_size / sizeof(CgbnPair) << std::endl;
      encrypted_gh_pairs_ = (CgbnPair*)malloc(remaining_size);
      memcpy(encrypted_gh_pairs_, pointer, remaining_size);
      if (debug_) std::cout << "setGHPairs is done " << std::endl;
    }

    void clearGHPairs() {
      if (debug_) std::cout << "clearGHPairs is called" << std::endl;
      if (encrypted_gh_pairs_) {
        //cudaFree(encrypted_gh_pairs_);
        free(encrypted_gh_pairs_);
        encrypted_gh_pairs_ = nullptr;
      }
      if (bin_array_) {
        free(bin_array_);
        bin_array_ = nullptr;
      }
      if (bin_length_) {
        free(bin_length_);
        bin_length_ = nullptr;
      }
      if (bin_start_idx_) {
        free(bin_start_idx_);
        bin_start_idx_ = nullptr;
      }
      if (debug_) std::cout << "clearGHPairs is finished" << std::endl;
    }

    Buffer createBuffer(
      bool has_key_flag,
      cgbn_mem_t<bits>* key_ptr,
      size_t key_size,
      uint64_t rand_seed,
      size_t rand_seed_size,
      cgbn_mem_t<bits>* d_ciphers_ptr,
      size_t payload_size
    ) {
        if (debug_) std::cout << "createBuffer is called" << std::endl;
        // Calculate header size and total buffer size
        size_t header_size = sizeof(BufferHeader2);
        size_t mem_size = header_size + key_size + rand_seed_size + payload_size;

        // Allocate buffer
        void* buffer = malloc(mem_size);
        if (!buffer) {
          std::cout << "bad alloc with buffer" << std::endl;
          throw std::bad_alloc();
        }

        // Construct header
        BufferHeader2 header;
        header.has_key = has_key_flag;
        header.key_size = key_size;
        header.rand_seed_size = rand_seed_size;

        // Copy header to buffer
        memcpy(buffer, &header, header_size);

        // Copy the key (if present)
        if (has_key_flag) {
          memcpy((char*)buffer + header_size, key_ptr, key_size);
          memcpy((char*)buffer + header_size + key_size, &rand_seed, rand_seed_size);
        }

        // Copy the payload
        cudaMemcpy((char*)buffer + header_size + key_size + rand_seed_size, d_ciphers_ptr, payload_size, cudaMemcpyDeviceToHost);

        Buffer result(buffer, mem_size, true);

        return result;
    }

    Buffer EncryptVector(const std::vector<double>& cleartext) override {
      if (debug_) std::cout << "Calling EncryptVector with count " << cleartext.size() << std::endl;
      if (endec_ptr_ != nullptr) {
        delete endec_ptr_;
      }
      endec_ptr_ = new Endec(PRECISION, debug_);

      size_t count = cleartext.size();
      int byte_length = bits / 8;
      size_t mem_size = sizeof(cgbn_mem_t<bits>) * count;
      cgbn_mem_t<bits>* h_ptr=(cgbn_mem_t<bits>* )malloc(mem_size);
      if (debug_) std::cout << "h_ptr size is " << mem_size << " indata size is " << count * byte_length << std::endl;
      for (size_t i = 0; i < count; ++i) {
        mpz_t n;
        mpz_init(n);

        endec_ptr_->encode(n, cleartext[i]);
        store2Cgbn(h_ptr + i, n);

        mpz_clear(n);
      }

      cgbn_mem_t<bits>* d_plains_ptr;
      cgbn_mem_t<bits>* d_ciphers_ptr;
      ck(cudaMalloc((void **)&d_plains_ptr, mem_size));
      ck(cudaMalloc((void **)&d_ciphers_ptr, mem_size));
      cudaMemcpy(d_plains_ptr, h_ptr, mem_size, cudaMemcpyHostToDevice);

      if (!paillier_cipher_ptr_->has_prv_key) {
#ifdef TIME
        CudaTimer cuda_timer(0);
        float gen_time=0;
        cuda_timer.start();
#endif
        if (debug_) std::cout<<"Gen KeyPair with bits: " << bits << std::endl;
        paillier_cipher_ptr_->genKeypair();
#ifdef TIME
        gen_time += cuda_timer.stop();
        std::cout<<"Gen KeyPair Time "<< gen_time <<" MS"<<std::endl;
#endif
      }

      paillier_cipher_ptr_->encrypt<TPI,TPB>(d_plains_ptr, d_ciphers_ptr, count);

      // get pub_key n
      mpz_t n;
      mpz_init(n);
      size_t key_size = sizeof(cgbn_mem_t<bits>);
      paillier_cipher_ptr_->getN(n);
      store2Cgbn(h_ptr, n);
      mpz_clear(n);

      // get rand_seed
      size_t rand_seed_size = sizeof(uint64_t);
      uint64_t rand_seed = paillier_cipher_ptr_->get_rand_seed();

      Buffer result = createBuffer(true, h_ptr, key_size, rand_seed, rand_seed_size, d_ciphers_ptr, mem_size);

      cudaFree(d_plains_ptr);
      cudaFree(d_ciphers_ptr);
      free(h_ptr);

      return result;
    }

    std::vector<double> DecryptVector(const std::vector<Buffer>& ciphertext) override {
      if (debug_) std::cout << "Calling DecryptVector" << std::endl;
      size_t mem_size = 0;
      for (int i = 0; i < ciphertext.size(); ++i) {
        mem_size += ciphertext[i].buf_size;
        if (ciphertext[i].buf_size != 2 * sizeof(cgbn_mem_t<bits>)) {
          std::cout << "buf_size is " << ciphertext[i].buf_size << std::endl;
          std::cout << "expected buf_size is " << 2 * sizeof(cgbn_mem_t<bits>) << std::endl;
          std::cout << "Fatal Error" << std::endl;
        }
      }

      size_t count = mem_size / sizeof(cgbn_mem_t<bits>);
      cgbn_mem_t<bits>* h_ptr=(cgbn_mem_t<bits>* )malloc(mem_size);
      if (debug_) std::cout << "h_ptr size is " << mem_size << " how many gh is " << count << std::endl;
      

      cgbn_mem_t<bits>* d_plains_ptr;
      cgbn_mem_t<bits>* d_ciphers_ptr;
      ck(cudaMalloc((void **)&d_plains_ptr, mem_size));
      ck(cudaMalloc((void **)&d_ciphers_ptr, mem_size));
      
      size_t offset = 0;
      for (int i = 0; i < ciphertext.size(); ++i) {
        cudaMemcpy(d_ciphers_ptr + offset, ciphertext[i].buffer, ciphertext[i].buf_size, cudaMemcpyHostToDevice);
        offset += ciphertext[i].buf_size / sizeof(cgbn_mem_t<bits>);
      }

      if (!paillier_cipher_ptr_->has_prv_key) {
        std::cout << "Can't call DecryptVector if paillier does not have private key." << std::endl;
        throw std::runtime_error("Can't call DecryptVector if paillier does not have private key.");
      }


      paillier_cipher_ptr_->decrypt<TPI,TPB>(d_ciphers_ptr, d_plains_ptr, count);
      cudaMemcpy(h_ptr, d_plains_ptr, mem_size, cudaMemcpyDeviceToHost);

      std::vector<double> result;
      result.resize(count);
      for (size_t i = 0; i < count; ++i) {
        mpz_t n;
        mpz_init(n);
        store2Gmp(n, h_ptr + i);
        double output_num = endec_ptr_->decode(n);
        result[i] = output_num;
        mpz_clear(n);
      }
      cudaFree(d_plains_ptr);
      cudaFree(d_ciphers_ptr);
      free(h_ptr);
      return result;
    }

    void reserveCellTable(size_t table_size) {
      if (table_size > cell_table_size) {
        if (cell_table) {
          free(cell_table);
        }
        if (d_cell_table) {
          cudaFree(d_cell_table);
        }
        if (debug_) std::cout << overall_timer_.now() << ": malloc cell_table" << std::endl;
        cell_table = (CgbnPair*)malloc(table_size);
        ck(cudaMalloc((void **)&d_cell_table, table_size));
        if (debug_) std::cout << overall_timer_.now() << ": after malloc cell_table" << std::endl;
        cell_table_size = table_size;
      }
    }

    void fillArray(
      CgbnPair* cell_table,
      std::size_t total_bin_size,
      int* rbt,
      int num_cols,
      int &last_col_used,
      int &num_tuples_filled,
      int tuple_length = 2
    ) {
      last_col_used = -1;
      int num_tuples_per_row = num_cols / tuple_length;

      for (auto j = 0; j < num_tuples_per_row; ++j) {
        rbt[j] = -1;
      } 

      Context ctx = Context(total_bin_size, bin_length_);

      int remaining_slots = num_tuples_per_row;
      while (remaining_slots > 0) {
        int bid = 0;
        int start_idx = -1;
        int end_idx = -1;

        ctx.get_next_chunk(bid, start_idx, end_idx, remaining_slots, tuple_length);

        if (start_idx == -1) {
          return;
        }
        int count = end_idx - start_idx + 1;
        int tuple_count = count / tuple_length;
        int cell_table_idx = (num_tuples_per_row - remaining_slots) * tuple_length;

        memcpy(cell_table + cell_table_idx, bin_array_ + bin_start_idx_[bid] + start_idx, count * sizeof(CgbnPair));
        for (auto i = 0; i < tuple_count; ++i) {
          rbt[num_tuples_per_row - remaining_slots + i] = bid;
        }
        num_tuples_filled += tuple_count;
        remaining_slots -= tuple_count;

        last_col_used = end_idx / tuple_length;
      }

    }

    void processResult(
      CgbnPair* cell_table,
      int* rbt,
      int num_cols,
      int tuple_length = 2
      ) {

      int num_tuples_per_row = num_cols / tuple_length;

      for (auto j = 0; j < num_tuples_per_row; ++j) {
        int bid = rbt[j];
        if (bid < 0) {
          return;
        }
        bin_array_[bin_start_idx_[bid] + bin_length_[bid]] = cell_table[j * tuple_length];
        bin_length_[bid] += 1;
      }


    }

    size_t prepareBinArray(const std::uint64_t *ridx, const std::size_t size) {
      auto total_bin_size = cuts_.back();
      auto num_feature = cuts_.size() - 1;
      size_t result = 0;

#ifdef TIME
      Timer timer;
      timer.start();
#endif

      // first pass to get size
      for (std::size_t f = 0; f < num_feature; f++) {
        for (std::size_t j = 0; j < size; j++) {
          auto row_id = ridx[j];
          int bin_idx = bin_idx_vec_[f + num_feature * row_id];
          if ((bin_idx < 0) || (bin_idx >= total_bin_size)) {
            continue;
          }
          bin_length_[bin_idx]++;
          result++;
        }
      }

      size_t bin_offset = 0;
      for (auto i = 0; i < total_bin_size; i++) {
        bin_start_idx_[i] = bin_offset;
        bin_offset += bin_length_[i];
      }

#ifdef TIME
      timer.stop();
      std::cout << "First pass time: " << timer.duration() << std::endl;
      timer.start();
#endif

      if (bin_array_) {
        free(bin_array_);
        bin_array_ = nullptr;
      }
      bin_array_ = (CgbnPair*)malloc(result * sizeof(CgbnPair));

      std::size_t* bin_insert_index = (std::size_t*)calloc(total_bin_size, sizeof(size_t));

#ifdef TIME
      timer.stop();
      if (debug_) std::cout << "malloc bin array time: " << timer.duration() << std::endl;
      timer.start();
#endif

      // second pass assignment      
      for (auto f = 0; f < num_feature; f++) {
        for (auto j = 0; j < size; j++) {
          auto row_id = ridx[j];
          int bin_idx = bin_idx_vec_[f + num_feature * row_id];
          if ((bin_idx < 0) || (bin_idx >= total_bin_size)) {
            continue;
          }

          memcpy(&bin_array_[bin_start_idx_[bin_idx] + bin_insert_index[bin_idx]], &encrypted_gh_pairs_[row_id], sizeof(CgbnPair));
          bin_insert_index[bin_idx]++;
        }
      }

#ifdef TIME
      timer.stop();
      std::cout << "Second pass time: " << timer.duration() << std::endl;
#endif

      for (auto i = 0; i < total_bin_size; i++) {

        if (bin_length_[i] != bin_insert_index[i]) {
          std::cout << "bin_length_ " << bin_length_[i] << " bin_insert_index " << bin_insert_index[i] << std::endl;
          throw std::runtime_error("prepareBinArray logic error."); 
        }
      }
      free(bin_insert_index);

      return result;
    }

    void fillResult(std::vector<Buffer>& result, size_t total_bin_size) {
      for (auto bid = 0; bid < total_bin_size; ++bid) {
        CgbnPair hist;
        CgbnPair* data = (CgbnPair*)malloc(sizeof(CgbnPair));
        if (bin_length_[bid] == 0) {
          hist = paillier_cipher_ptr_->get_encrypted_zero();
        } else {
          hist = bin_array_[bin_start_idx_[bid]];
        }
        *data = hist;
        Buffer buffer((void*)(data), sizeof(CgbnPair), true);
        result[bid] = buffer; // Add the Buffer object to the result map

      }
    }

    void AddGHPairs(std::vector<Buffer>& result, const std::uint64_t *ridx, const std::size_t size) override {

      overall_timer_.start();
      auto total_bin_size = cuts_.back();

      if (debug_) std::cout << overall_timer_.now() << ": Calling AddGHPairs with total_bin_size " << total_bin_size << std::endl;
      if (!encrypted_gh_pairs_) {
        setGHPairs();
      }

      if (!paillier_cipher_ptr_->has_pub_key) {
        std::cout << "Can't call AddGHPairs if paillier does not have public key." << std::endl;
        throw std::runtime_error("Can't call AddGHPairs if paillier does not have public key.");
      }

      int tuple_length = 2;
      size_t IPB = TPB / TPI;
      //unsigned int max_blocks = 1 << 20; // limitation of hardware memory (GPU)
      size_t max_num_of_kernel_launch_permitted = 1 << 22;
      size_t max_num_of_instances_per_launch = max_num_of_kernel_launch_permitted * tuple_length; // maximum numbers that can fit into GPU memory
      unsigned int max_blocks = max_num_of_instances_per_launch / IPB;

      if (debug_) std::cout << overall_timer_.now() << ": Preparing bin_xxx" << std::endl;

#ifdef TIME
      Timer timer;
      timer.start();
#endif

      if (debug_) std::cout << overall_timer_.now() << ": before calloc" << std::endl;
      if (!bin_length_) {
        bin_length_ = (size_t*)calloc(total_bin_size, sizeof(size_t));
        bin_start_idx_ = (size_t*)malloc(total_bin_size * sizeof(size_t));
      }
      
      if (debug_) std::cout << overall_timer_.now() << ": before prepareBinArray" << std::endl;
      size_t total_sample_ids = prepareBinArray(ridx, size);
      if (debug_) std::cout << overall_timer_.now() << ": after prepareBinArray, max_num_of_instances_per_launch: " << max_num_of_instances_per_launch << " , total_sample_ids: " << total_sample_ids << std::endl;

      // weird situation where all things are empty
      if (total_sample_ids == 0) {
        fillResult(result, total_bin_size);
        return;
      }

      int num_tuples_per_row = std::min(total_sample_ids, max_num_of_instances_per_launch) / tuple_length; 
      int num_cols = num_tuples_per_row * tuple_length; // needs to be a multiple of tuple
      size_t table_size = sizeof(CgbnPair) * num_cols;
      if (debug_) std::cout << "table mem size is " << table_size << std::endl;

      if (!cell_table) {
        reserveCellTable(table_size);
      }

      if (debug_) std::cout << overall_timer_.now() << ": Finished preparing bin_xxx, total_sample_ids is " << total_sample_ids << " total_bin_size is " << total_bin_size << std::endl;


#ifdef TIME
      timer.stop();
      double elapsed = timer.duration();
      std::cout<< overall_timer_.now() << ": prepare bin_xxx Time "<< elapsed <<" US"<<std::endl;
      total_prepare_bin_time_ += elapsed;
#endif

      if (debug_) std::cout << overall_timer_.now() << ": max_num_of_instances_per_launch: " << max_num_of_instances_per_launch << " num_cols: " << num_cols << std::endl;

      int* rbt = (int*)malloc(sizeof(int) * num_tuples_per_row);

      int last_col = 0;
      int num_tuples_in_table = 0;
      int reduce_round = 0;

      while (true) {
        num_tuples_in_table = 0;

#ifdef TIME
        timer.start();
#endif
        if (debug_) std::cout << overall_timer_.now() << ": Start fillArray for reduce_round " << reduce_round << std::endl;
        fillArray(cell_table, total_bin_size, rbt, num_cols, last_col, num_tuples_in_table, tuple_length);
        if (debug_) std::cout << overall_timer_.now() << ": End fillArray for reduce_round " << reduce_round << std::endl;
        if (debug_) std::cout << overall_timer_.now() << " last col " << last_col << " num_tuples_in_table " << num_tuples_in_table << std::endl;

#ifdef TIME
        timer.stop();
        std::cout << overall_timer_.now() << ": fillArray Time "<< timer.duration() <<" US"<<std::endl;
#endif

        if (last_col < 0) {
          break;
        }

#ifdef TIME
        timer.start();
#endif
        table_size = sizeof(CgbnPair) * num_tuples_in_table * tuple_length;
        cudaMemcpy(d_cell_table, cell_table, table_size, cudaMemcpyHostToDevice);
#ifdef TIME
        timer.stop();
        std::cout<< overall_timer_.now() << ":cudaMemcpy cell_table cudaMemcpyHostToDevice Time "<< timer.duration() <<" US"<<std::endl;
        timer.start();
#endif
        paillier_cipher_ptr_->agg_tuple<TPI, TPB>(d_cell_table, num_tuples_in_table * tuple_length, max_blocks);
#ifdef TIME
        timer.stop();
        elapsed = timer.duration();
        std::cout<< overall_timer_.now() << ":agg_tuple Time "<< elapsed <<" US"<<std::endl;
        total_agg_time_ += elapsed;
        timer.start();
#endif
        cudaMemcpy(cell_table, d_cell_table, table_size, cudaMemcpyDeviceToHost);
#ifdef TIME
        timer.stop();
        std::cout<< overall_timer_.now() << ":cudaMemcpy cell_table cudaMemcpyDeviceToHost Time "<< timer.duration() <<" US"<<std::endl;
#endif

#ifdef TIME
        timer.start();
#endif
        processResult(cell_table, rbt, num_cols, tuple_length);
#ifdef TIME
        timer.stop();
        std::cout<< overall_timer_.now() << ":processResult Time "<< timer.duration() <<" US"<<std::endl;
#endif

        reduce_round += 1;
        
      }

      // Get the final result
      fillResult(result, total_bin_size);

      if (debug_) std::cout << overall_timer_.now() << ":Finish AddGHPairs" << std::endl;
      if (encrypted_gh_pairs_) {
        clearGHPairs();
      }

      free(rbt);
      overall_timer_.stop();
      if (debug_) std::cout << overall_timer_.now() << ":AddGHPairs Total Time "<< overall_timer_.duration() <<" US"<<std::endl;

    }

};
} // namespace nvflare

#endif // CUDA_PLUGIN_H
