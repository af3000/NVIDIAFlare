(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[874],{27484:function(t){t.exports=function(){"use strict";var t=1e3,e=6e4,n=36e5,r="millisecond",i="second",s="minute",o="hour",u="day",a="week",c="month",l="quarter",f="year",h="date",d="Invalid Date",p=/^(\d{4})[-/]?(\d{1,2})?[-/]?(\d{0,2})[Tt\s]*(\d{1,2})?:?(\d{1,2})?:?(\d{1,2})?[.:]?(\d+)?$/,m=/\[([^\]]+)]|Y{1,4}|M{1,4}|D{1,2}|d{1,4}|H{1,2}|h{1,2}|a|A|m{1,2}|s{1,2}|Z{1,2}|SSS/g,g={name:"en",weekdays:"Sunday_Monday_Tuesday_Wednesday_Thursday_Friday_Saturday".split("_"),months:"January_February_March_April_May_June_July_August_September_October_November_December".split("_"),ordinal:function(t){var e=["th","st","nd","rd"],n=t%100;return"["+t+(e[(n-20)%10]||e[n]||e[0])+"]"}},v=function(t,e,n){var r=String(t);return!r||r.length>=e?t:""+Array(e+1-r.length).join(n)+t},$={s:v,z:function(t){var e=-t.utcOffset(),n=Math.abs(e),r=Math.floor(n/60),i=n%60;return(e<=0?"+":"-")+v(r,2,"0")+":"+v(i,2,"0")},m:function t(e,n){if(e.date()<n.date())return-t(n,e);var r=12*(n.year()-e.year())+(n.month()-e.month()),i=e.clone().add(r,c),s=n-i<0,o=e.clone().add(r+(s?-1:1),c);return+(-(r+(n-i)/(s?i-o:o-i))||0)},a:function(t){return t<0?Math.ceil(t)||0:Math.floor(t)},p:function(t){return{M:c,y:f,w:a,d:u,D:h,h:o,m:s,s:i,ms:r,Q:l}[t]||String(t||"").toLowerCase().replace(/s$/,"")},u:function(t){return void 0===t}},M="en",y={};y[M]=g;var x=function(t){return t instanceof D},S=function t(e,n,r){var i;if(!e)return M;if("string"==typeof e){var s=e.toLowerCase();y[s]&&(i=s),n&&(y[s]=n,i=s);var o=e.split("-");if(!i&&o.length>1)return t(o[0])}else{var u=e.name;y[u]=e,i=u}return!r&&i&&(M=i),i||!r&&M},w=function(t,e){if(x(t))return t.clone();var n="object"==typeof e?e:{};return n.date=t,n.args=arguments,new D(n)},j=$;j.l=S,j.i=x,j.w=function(t,e){return w(t,{locale:e.$L,utc:e.$u,x:e.$x,$offset:e.$offset})};var D=function(){function g(t){this.$L=S(t.locale,null,!0),this.parse(t)}var v=g.prototype;return v.parse=function(t){this.$d=function(t){var e=t.date,n=t.utc;if(null===e)return new Date(NaN);if(j.u(e))return new Date;if(e instanceof Date)return new Date(e);if("string"==typeof e&&!/Z$/i.test(e)){var r=e.match(p);if(r){var i=r[2]-1||0,s=(r[7]||"0").substring(0,3);return n?new Date(Date.UTC(r[1],i,r[3]||1,r[4]||0,r[5]||0,r[6]||0,s)):new Date(r[1],i,r[3]||1,r[4]||0,r[5]||0,r[6]||0,s)}}return new Date(e)}(t),this.$x=t.x||{},this.init()},v.init=function(){var t=this.$d;this.$y=t.getFullYear(),this.$M=t.getMonth(),this.$D=t.getDate(),this.$W=t.getDay(),this.$H=t.getHours(),this.$m=t.getMinutes(),this.$s=t.getSeconds(),this.$ms=t.getMilliseconds()},v.$utils=function(){return j},v.isValid=function(){return!(this.$d.toString()===d)},v.isSame=function(t,e){var n=w(t);return this.startOf(e)<=n&&n<=this.endOf(e)},v.isAfter=function(t,e){return w(t)<this.startOf(e)},v.isBefore=function(t,e){return this.endOf(e)<w(t)},v.$g=function(t,e,n){return j.u(t)?this[e]:this.set(n,t)},v.unix=function(){return Math.floor(this.valueOf()/1e3)},v.valueOf=function(){return this.$d.getTime()},v.startOf=function(t,e){var n=this,r=!!j.u(e)||e,l=j.p(t),d=function(t,e){var i=j.w(n.$u?Date.UTC(n.$y,e,t):new Date(n.$y,e,t),n);return r?i:i.endOf(u)},p=function(t,e){return j.w(n.toDate()[t].apply(n.toDate("s"),(r?[0,0,0,0]:[23,59,59,999]).slice(e)),n)},m=this.$W,g=this.$M,v=this.$D,$="set"+(this.$u?"UTC":"");switch(l){case f:return r?d(1,0):d(31,11);case c:return r?d(1,g):d(0,g+1);case a:var M=this.$locale().weekStart||0,y=(m<M?m+7:m)-M;return d(r?v-y:v+(6-y),g);case u:case h:return p($+"Hours",0);case o:return p($+"Minutes",1);case s:return p($+"Seconds",2);case i:return p($+"Milliseconds",3);default:return this.clone()}},v.endOf=function(t){return this.startOf(t,!1)},v.$set=function(t,e){var n,a=j.p(t),l="set"+(this.$u?"UTC":""),d=(n={},n[u]=l+"Date",n[h]=l+"Date",n[c]=l+"Month",n[f]=l+"FullYear",n[o]=l+"Hours",n[s]=l+"Minutes",n[i]=l+"Seconds",n[r]=l+"Milliseconds",n)[a],p=a===u?this.$D+(e-this.$W):e;if(a===c||a===f){var m=this.clone().set(h,1);m.$d[d](p),m.init(),this.$d=m.set(h,Math.min(this.$D,m.daysInMonth())).$d}else d&&this.$d[d](p);return this.init(),this},v.set=function(t,e){return this.clone().$set(t,e)},v.get=function(t){return this[j.p(t)]()},v.add=function(r,l){var h,d=this;r=Number(r);var p=j.p(l),m=function(t){var e=w(d);return j.w(e.date(e.date()+Math.round(t*r)),d)};if(p===c)return this.set(c,this.$M+r);if(p===f)return this.set(f,this.$y+r);if(p===u)return m(1);if(p===a)return m(7);var g=(h={},h[s]=e,h[o]=n,h[i]=t,h)[p]||1,v=this.$d.getTime()+r*g;return j.w(v,this)},v.subtract=function(t,e){return this.add(-1*t,e)},v.format=function(t){var e=this,n=this.$locale();if(!this.isValid())return n.invalidDate||d;var r=t||"YYYY-MM-DDTHH:mm:ssZ",i=j.z(this),s=this.$H,o=this.$m,u=this.$M,a=n.weekdays,c=n.months,l=function(t,n,i,s){return t&&(t[n]||t(e,r))||i[n].slice(0,s)},f=function(t){return j.s(s%12||12,t,"0")},h=n.meridiem||function(t,e,n){var r=t<12?"AM":"PM";return n?r.toLowerCase():r},p={YY:String(this.$y).slice(-2),YYYY:this.$y,M:u+1,MM:j.s(u+1,2,"0"),MMM:l(n.monthsShort,u,c,3),MMMM:l(c,u),D:this.$D,DD:j.s(this.$D,2,"0"),d:String(this.$W),dd:l(n.weekdaysMin,this.$W,a,2),ddd:l(n.weekdaysShort,this.$W,a,3),dddd:a[this.$W],H:String(s),HH:j.s(s,2,"0"),h:f(1),hh:f(2),a:h(s,o,!0),A:h(s,o,!1),m:String(o),mm:j.s(o,2,"0"),s:String(this.$s),ss:j.s(this.$s,2,"0"),SSS:j.s(this.$ms,3,"0"),Z:i};return r.replace(m,(function(t,e){return e||p[t]||i.replace(":","")}))},v.utcOffset=function(){return 15*-Math.round(this.$d.getTimezoneOffset()/15)},v.diff=function(r,h,d){var p,m=j.p(h),g=w(r),v=(g.utcOffset()-this.utcOffset())*e,$=this-g,M=j.m(this,g);return M=(p={},p[f]=M/12,p[c]=M,p[l]=M/3,p[a]=($-v)/6048e5,p[u]=($-v)/864e5,p[o]=$/n,p[s]=$/e,p[i]=$/t,p)[m]||$,d?M:j.a(M)},v.daysInMonth=function(){return this.endOf(c).$D},v.$locale=function(){return y[this.$L]},v.locale=function(t,e){if(!t)return this.$L;var n=this.clone(),r=S(t,e,!0);return r&&(n.$L=r),n},v.clone=function(){return j.w(this.$d,this)},v.toDate=function(){return new Date(this.valueOf())},v.toJSON=function(){return this.isValid()?this.toISOString():null},v.toISOString=function(){return this.$d.toISOString()},v.toString=function(){return this.$d.toUTCString()},g}(),b=D.prototype;return w.prototype=b,[["$ms",r],["$s",i],["$m",s],["$H",o],["$W",u],["$M",c],["$y",f],["$D",h]].forEach((function(t){b[t[1]]=function(e){return this.$g(e,t[0],t[1])}})),w.extend=function(t,e){return t.$i||(t(e,D,w),t.$i=!0),w},w.locale=S,w.isDayjs=x,w.unix=function(t){return w(1e3*t)},w.en=y[M],w.Ls=y,w.p={},w}()},89924:function(t,e,n){"use strict";n.d(e,{y:function(){return v}});var r=n(9669),i=n.n(r),s=n(84506),o=n(68253),u=n(35823),a=n.n(u),c=s,l=i().create({baseURL:c.url_root+"/api/v1/",headers:{"Access-Control-Allow-Origin":"*"}});l.interceptors.request.use((function(t){return t.headers.Authorization="Bearer "+(0,o.Gg)().user.token,t}),(function(t){console.log("Interceptor request error: "+t)})),l.interceptors.response.use((function(t){return t}),(function(t){throw console.log(" AXIOS error: "),console.log(t),401===t.response.status&&(0,o.KY)("","",-1,0,"",!0),403===t.response.status&&console.log("Error: "+t.response.data.status),404===t.response.status&&console.log("Error: "+t.response.data.status),409===t.response.status&&console.log("Error: "+t.response.data.status),422===t.response.status&&(0,o.KY)("","",-1,0,"",!0),t}));var f=function(t){return t.data},h=function(t){return l.get(t).then(f)},d=function(t,e,n){return l.post(t,{pin:n},{responseType:"blob"}).then((function(t){e=t.headers["content-disposition"].split('"')[1],a()(t.data,e)}))},p=function(t,e){return l.post(t,e).then(f)},m=function(t,e){return l.patch(t,e).then(f)},g=function(t){return l.delete(t).then(f)},v={login:function(t){return p("login",t)},getUsers:function(){return h("users")},getUser:function(t){return h("users/".concat(t))},getUserStartupKit:function(t,e,n){return d("users/".concat(t,"/blob"),e,n)},getClientStartupKit:function(t,e,n){return d("clients/".concat(t,"/blob"),e,n)},getOverseerStartupKit:function(t,e){return d("overseer/blob",t,e)},getServerStartupKit:function(t,e,n){return d("servers/".concat(t,"/blob"),e,n)},getClients:function(){return h("clients")},getProject:function(){return h("project")},postUser:function(t){return p("users",t)},patchUser:function(t,e){return m("users/".concat(t),e)},deleteUser:function(t){return g("users/".concat(t))},postClient:function(t){return p("clients",t)},patchClient:function(t,e){return m("clients/".concat(t),e)},deleteClient:function(t){return g("clients/".concat(t))},patchProject:function(t){return m("project",t)},getServer:function(){return h("server")},patchServer:function(t){return m("server",t)}}},57061:function(t,e,n){"use strict";n.d(e,{Z:function(){return C}});var r=n(50029),i=n(87794),s=n.n(i),o=n(41664),u=n.n(o),a=n(29224),c=n.n(a),l=n(70491),f=n.n(l),h=n(86188),d=n.n(h),p=n(29430),m=p.default.div.withConfig({displayName:"styles__StyledLayout",componentId:"sc-xczy9u-0"})(["overflow:hidden;height:100%;width:100%;margin:0;padding:0;display:flex;flex-wrap:wrap;.menu{height:auto;}.content-header{flex:0 0 80px;}"]),g=p.default.div.withConfig({displayName:"styles__StyledContent",componentId:"sc-xczy9u-1"})(["display:flex;flex-direction:column;flex:1 1 0%;overflow:auto;height:calc(100% - 3rem);.inlineeditlarger{padding:10px;}.inlineedit{padding:10px;margin:-10px;}.content-wrapper{padding:",";min-height:800px;}"],(function(t){return t.theme.spacing.four})),v=n(11163),$=n(84506),M=n(67294),y=n(68253),x=n(13258),S=n.n(x),w=n(5801),j=n.n(w),D=n(89924),b=n(85893),C=function(t){var e=t.children,n=t.headerChildren,i=t.title,o=(0,v.useRouter)(),a=o.pathname,l=o.push,p=$,w=(0,M.useState)(),C=w[0],O=w[1],I=(0,y.Gg)();(0,M.useEffect)((function(){D.y.getProject().then((function(t){O(t.project)}))}),[]);var _=function(){var t=(0,r.Z)(s().mark((function t(){return s().wrap((function(t){for(;;)switch(t.prev=t.next){case 0:(0,y.KY)("none","",-1,0),l("/");case 2:case"end":return t.stop()}}),t)})));return function(){return t.apply(this,arguments)}}();return(0,b.jsxs)(m,{children:[(0,b.jsx)(c(),{app:null===C||void 0===C?void 0:C.short_name,appBarActions:I.user.role>0?(0,b.jsxs)("div",{style:{display:"flex",flexDirection:"row",alignItems:"center",marginRight:10},children:[p.demo&&(0,b.jsx)("div",{children:"DEMO MODE"}),(0,b.jsx)(S(),{parentElement:(0,b.jsx)(j(),{icon:{name:"AccountCircleGenericUser",color:"white",size:22},shape:"circle",variant:"link",className:"logout-link"}),position:"top-right",children:(0,b.jsxs)(b.Fragment,{children:[(0,b.jsx)(x.ActionMenuItem,{label:"Logout",onClick:_}),!1]})})]}):(0,b.jsx)(b.Fragment,{})}),(0,b.jsxs)(d(),{className:"menu",itemMatchPattern:function(t){return t===a},itemRenderer:function(t){var e=t.title,n=t.href;return(0,b.jsx)(u(),{href:n,children:e})},location:a,children:[0==I.user.role&&(0,b.jsxs)(h.MenuContent,{children:[(0,b.jsx)(h.MenuItem,{href:"/",icon:{name:"AccountUser"},title:"Login"}),(0,b.jsx)(h.MenuItem,{href:"/registration-form",icon:{name:"ObjectsClipboardEdit"},title:"User Registration Form"})]}),4==I.user.role&&(0,b.jsxs)(h.MenuContent,{children:[(0,b.jsx)(h.MenuItem,{href:"/",icon:{name:"ViewList"},title:"Project Home"}),(0,b.jsx)(h.MenuItem,{href:"/user-dashboard",icon:{name:"ServerEdit"},title:"My Info"}),(0,b.jsx)(h.MenuItem,{href:"/project-admin-dashboard",icon:{name:"AccountGroupShieldAdd"},title:"Users Dashboard"}),(0,b.jsx)(h.MenuItem,{href:"/site-dashboard",icon:{name:"ConnectionNetworkComputers2"},title:"Client Sites"}),(0,b.jsx)(h.MenuItem,{href:"/project-configuration",icon:{name:"SettingsCog"},title:"Project Configuration"}),(0,b.jsx)(h.MenuItem,{href:"/server-config",icon:{name:"ConnectionServerNetwork1"},title:"Server Configuration"}),(0,b.jsx)(h.MenuItem,{href:"/downloads",icon:{name:"ActionsDownload"},title:"Downloads"}),(0,b.jsx)(h.MenuItem,{href:"/logout",icon:{name:"PlaybackStop"},title:"Logout"})]}),(1==I.user.role||2==I.user.role||3==I.user.role)&&(0,b.jsxs)(h.MenuContent,{children:[(0,b.jsx)(h.MenuItem,{href:"/",icon:{name:"ViewList"},title:"Project Home Page"}),(0,b.jsx)(h.MenuItem,{href:"/user-dashboard",icon:{name:"ServerEdit"},title:"My Info"}),(0,b.jsx)(h.MenuItem,{href:"/downloads",icon:{name:"ActionsDownload"},title:"Downloads"}),(0,b.jsx)(h.MenuItem,{href:"/logout",icon:{name:"PlaybackStop"},title:"Logout"})]}),(0,b.jsx)(h.MenuFooter,{})]}),(0,b.jsxs)(g,{children:[(0,b.jsx)(f(),{className:"content-header",title:i,children:n}),(0,b.jsx)("div",{className:"content-wrapper",children:e})]})]})}},68253:function(t,e,n){"use strict";n.d(e,{Gg:function(){return o},KY:function(){return i},a5:function(){return s}});var r={user:{email:"",token:"",id:-1,role:0},status:"unauthenticated"};function i(t,e,n,i,s){var o=arguments.length>5&&void 0!==arguments[5]&&arguments[5];return r={user:{email:t,token:e,id:n,role:i,org:s},expired:o,status:0==i?"unauthenticated":"authenticated"},localStorage.setItem("session",JSON.stringify(r)),r}function s(t){return r={user:{email:r.user.email,token:r.user.token,id:r.user.id,role:t,org:r.user.org},expired:r.expired,status:r.status},localStorage.setItem("session",JSON.stringify(r)),r}function o(){var t=localStorage.getItem("session");return null!=t&&(r=JSON.parse(t)),r}},50029:function(t,e,n){"use strict";function r(t,e,n,r,i,s,o){try{var u=t[s](o),a=u.value}catch(c){return void n(c)}u.done?e(a):Promise.resolve(a).then(r,i)}function i(t){return function(){var e=this,n=arguments;return new Promise((function(i,s){var o=t.apply(e,n);function u(t){r(o,i,s,u,a,"next",t)}function a(t){r(o,i,s,u,a,"throw",t)}u(void 0)}))}}n.d(e,{Z:function(){return i}})},84506:function(t){"use strict";t.exports=JSON.parse('{"projectname":"New FL Project","demo":false,"url_root":"","arraydata":[{"name":"itemone"},{"name":"itemtwo"},{"name":"itemthree"}]}')}}]);