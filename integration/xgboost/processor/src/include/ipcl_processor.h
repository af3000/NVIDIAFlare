/**
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
#pragma once
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include "local_processor.h"
#include "ipcl/ipcl.hpp"

/*! \brief A processor using Intel's IPCL library */
class IpclProcessor: public LocalProcessor {
private:
    ipcl::KeyPair key_;
    ipcl::PublicKey public_key_;
    ipcl::CipherText zero_;
    int num_threads_;

public:

    void Initialize(bool active, std::map<std::string, std::string> params) override;

    Buffer EncryptVector(const std::vector<double>& cleartext) override;

    std::vector<double> DecryptVector(const std::vector<Buffer>& ciphertext) override;

    std::map<int, Buffer> AddGHPairs(const std::map<int, std::vector<int>>& sample_ids) override;

    void FreeEncryptedData(Buffer& ciphertext) override;
};
