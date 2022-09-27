(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[442],{88916:function(e,n,t){"use strict";var r=this&&this.__createBinding||(Object.create?function(e,n,t,r){void 0===r&&(r=t),Object.defineProperty(e,r,{enumerable:!0,get:function(){return n[t]}})}:function(e,n,t,r){void 0===r&&(r=t),e[r]=n[t]}),i=this&&this.__setModuleDefault||(Object.create?function(e,n){Object.defineProperty(e,"default",{enumerable:!0,value:n})}:function(e,n){e.default=n}),o=this&&this.__importStar||function(e){if(e&&e.__esModule)return e;var n={};if(null!=e)for(var t in e)"default"!==t&&Object.prototype.hasOwnProperty.call(e,t)&&r(n,e,t);return i(n,e),n},a=this&&this.__importDefault||function(e){return e&&e.__esModule?e:{default:e}};Object.defineProperty(n,"__esModule",{value:!0}),n.Styles=void 0;const s=o(t(67294)),u=o(t(31096)),l=t(7347),c=a(t(24777)),d=a(t(5801)),p=a(t(14167));n.Styles=p.default;const f=u.default.div`
  ${p.default.passwordContainer}
`;f.displayName="PasswordContainer";const m=(0,u.default)(c.default)``;m.displayName="Password";const g=(0,u.default)(d.default)`
  ${p.default.toggleVisibilityIcon}
`;g.displayName="VisibilityButton",n.default=function({autoFocus:e,className:n,disabled:t,form:r,id:i,inputMode:o,label:a,maxLength:c,minLength:d,name:p,onBlur:h,onCopy:_,onCut:v,onChange:y,onFocus:x,onKeyDown:j,onKeyPress:w,onKeyUp:b,onPaste:C,pattern:S,placeholder:I,readOnly:M,required:N,showVisibilityToggle:k=!0,tabIndex:z,title:P,validationMessage:A,value:B}){const O=(0,s.useContext)(l.KaizenThemeContext),[E,F]=(0,s.useState)(!1);return s.default.createElement(u.ThemeProvider,{theme:O},s.default.createElement(f,{className:n,"data-testid":"kui-password"},s.default.createElement(m,{autoCapitalize:"off",autoComplete:"on",autoFocus:e,disabled:t,form:r,id:i,inputMode:o,inputType:E?"singleLine":"password",label:a,maxLength:c,minLength:d,name:p,onBlur:h,onCopy:_,onCut:v,onChange:y,onFocus:x,onKeyDown:j,onKeyPress:w,onKeyUp:b,onPaste:C,pattern:S,placeholder:I,readOnly:M,required:N,showValidIcon:!1,spellCheck:!1,tabIndex:z,title:P,value:B,validationMessage:A}),k&&s.default.createElement(g,{onClick:()=>{F(!E)},icon:{name:E?"ActionsHide":"ActionsView"},variant:"link"})))}},14167:function(e,n){"use strict";Object.defineProperty(n,"__esModule",{value:!0});n.default={passwordContainer:"\n  position: relative;\n  width: 100%;\n",toggleVisibilityIcon:"\n  position: absolute;\n  right: 1rem;\n  top: 2.5rem;\n"}},89924:function(e,n,t){"use strict";t.d(n,{y:function(){return _}});var r=t(9669),i=t.n(r),o=t(84506),a=t(68253),s=t(35823),u=t.n(s),l=o,c=i().create({baseURL:l.url_root+"/api/v1/",headers:{"Access-Control-Allow-Origin":"*"}});c.interceptors.request.use((function(e){return e.headers.Authorization="Bearer "+(0,a.Gg)().user.token,e}),(function(e){console.log("Interceptor request error: "+e)})),c.interceptors.response.use((function(e){return e}),(function(e){throw console.log(" AXIOS error: "),console.log(e),401===e.response.status&&(0,a.KY)("","",-1,0,"",!0),403===e.response.status&&console.log("Error: "+e.response.data.status),409===e.response.status&&console.log("Error: "+e.response.data.status),422===e.response.status&&(0,a.KY)("","",-1,0,"",!0),e}));var d=function(e){return e.data},p=function(e){return c.get(e).then(d)},f=function(e,n,t){return c.post(e,{pin:t},{responseType:"blob"}).then((function(e){n=e.headers["content-disposition"].split('"')[1],u()(e.data,n)}))},m=function(e,n){return c.post(e,n).then(d)},g=function(e,n){return c.patch(e,n).then(d)},h=function(e){return c.delete(e).then(d)},_={login:function(e){return m("login",e)},getUsers:function(){return p("users")},getUser:function(e){return p("users/".concat(e))},getUserStartupKit:function(e,n,t){return f("users/".concat(e,"/blob"),n,t)},getClientStartupKit:function(e,n,t){return f("clients/".concat(e,"/blob"),n,t)},getOverseerStartupKit:function(e,n){return f("overseer/blob",e,n)},getServerStartupKit:function(e,n,t){return f("servers/".concat(e,"/blob"),n,t)},getClients:function(){return p("clients")},getProject:function(){return p("project")},postUser:function(e){return m("users",e)},patchUser:function(e,n){return g("users/".concat(e),n)},deleteUser:function(e){return h("users/".concat(e))},postClient:function(e){return m("clients",e)},patchClient:function(e,n){return g("clients/".concat(e),n)},deleteClient:function(e){return h("clients/".concat(e))},patchProject:function(e){return g("project",e)},getServer:function(){return p("server")},patchServer:function(e){return g("server",e)}}},57061:function(e,n,t){"use strict";t.d(n,{Z:function(){return M}});var r=t(50029),i=t(87794),o=t.n(i),a=t(41664),s=t.n(a),u=t(29224),l=t.n(u),c=t(70491),d=t.n(c),p=t(86188),f=t.n(p),m=t(31096),g=m.default.div.withConfig({displayName:"styles__StyledLayout",componentId:"sc-xczy9u-0"})(["overflow:hidden;height:100%;width:100%;margin:0;padding:0;display:flex;flex-wrap:wrap;.menu{height:auto;}.content-header{flex:0 0 80px;}"]),h=m.default.div.withConfig({displayName:"styles__StyledContent",componentId:"sc-xczy9u-1"})(["display:flex;flex-direction:column;flex:1 1 0%;overflow:auto;height:calc(100% - 3rem);.inlineeditlarger{padding:10px;}.inlineedit{padding:10px;margin:-10px;}.content-wrapper{padding:",";min-height:800px;}"],(function(e){return e.theme.spacing.four})),_=t(11163),v=t(84506),y=t(67294),x=t(68253),j=t(13258),w=t.n(j),b=t(5801),C=t.n(b),S=t(89924),I=t(85893),M=function(e){var n=e.children,t=e.headerChildren,i=e.title,a=(0,_.useRouter)(),u=a.pathname,c=a.push,m=v,b=(0,y.useState)(),M=b[0],N=b[1],k=(0,x.Gg)();(0,y.useEffect)((function(){S.y.getProject().then((function(e){N(e.project)}))}),[]);var z=function(){var e=(0,r.Z)(o().mark((function e(){return o().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:(0,x.KY)("none","",-1,0),c("/");case 2:case"end":return e.stop()}}),e)})));return function(){return e.apply(this,arguments)}}();return(0,I.jsxs)(g,{children:[(0,I.jsx)(l(),{app:null===M||void 0===M?void 0:M.short_name,appBarActions:k.user.role>0?(0,I.jsxs)("div",{style:{display:"flex",flexDirection:"row",alignItems:"center",marginRight:10},children:[m.demo&&(0,I.jsx)("div",{children:"DEMO MODE"}),(0,I.jsx)(w(),{parentElement:(0,I.jsx)(C(),{icon:{name:"AccountCircleGenericUser",color:"white",size:22},shape:"circle",variant:"link",className:"logout-link"}),position:"top-right",children:(0,I.jsxs)(I.Fragment,{children:[(0,I.jsx)(j.ActionMenuItem,{label:"Logout",onClick:z}),!1]})})]}):(0,I.jsx)(I.Fragment,{})}),(0,I.jsxs)(f(),{className:"menu",itemMatchPattern:function(e){return e===u},itemRenderer:function(e){var n=e.title,t=e.href;return(0,I.jsx)(s(),{href:t,children:n})},location:u,children:[0==k.user.role&&(0,I.jsxs)(p.MenuContent,{children:[(0,I.jsx)(p.MenuItem,{href:"/",icon:{name:"AccountUser"},title:"Login"}),(0,I.jsx)(p.MenuItem,{href:"/registration-form",icon:{name:"ObjectsClipboardEdit"},title:"User Registration Form"})]}),4==k.user.role&&(0,I.jsxs)(p.MenuContent,{children:[(0,I.jsx)(p.MenuItem,{href:"/",icon:{name:"ViewList"},title:"Project Home"}),(0,I.jsx)(p.MenuItem,{href:"/user-dashboard",icon:{name:"ServerEdit"},title:"My Info"}),(0,I.jsx)(p.MenuItem,{href:"/project-admin-dashboard",icon:{name:"AccountGroupShieldAdd"},title:"Users Dashboard"}),(0,I.jsx)(p.MenuItem,{href:"/site-dashboard",icon:{name:"ConnectionNetworkComputers2"},title:"Client Sites"}),(0,I.jsx)(p.MenuItem,{href:"/project-configuration",icon:{name:"SettingsCog"},title:"Project Configuration"}),(0,I.jsx)(p.MenuItem,{href:"/application-config",icon:{name:"WindowModule"},title:"Application Configuration"}),(0,I.jsx)(p.MenuItem,{href:"/server-config",icon:{name:"ConnectionServerNetwork1"},title:"Server Configuration"}),(0,I.jsx)(p.MenuItem,{href:"/downloads",icon:{name:"ActionsDownload"},title:"Downloads"}),(0,I.jsx)(p.MenuItem,{href:"/logout",icon:{name:"PlaybackStop"},title:"Logout"})]}),(1==k.user.role||2==k.user.role||3==k.user.role)&&(0,I.jsxs)(p.MenuContent,{children:[(0,I.jsx)(p.MenuItem,{href:"/",icon:{name:"ViewList"},title:"Project Home Page"}),(0,I.jsx)(p.MenuItem,{href:"/user-dashboard",icon:{name:"ServerEdit"},title:"My Info"}),(0,I.jsx)(p.MenuItem,{href:"/downloads",icon:{name:"ActionsDownload"},title:"Downloads"}),(0,I.jsx)(p.MenuItem,{href:"/logout",icon:{name:"PlaybackStop"},title:"Logout"})]}),(0,I.jsx)(p.MenuFooter,{})]}),(0,I.jsxs)(h,{children:[(0,I.jsx)(d(),{className:"content-header",title:i,children:t}),(0,I.jsx)("div",{className:"content-wrapper",children:n})]})]})}},56921:function(e,n,t){"use strict";t.d(n,{P:function(){return l},X:function(){return u}});var r=t(31096),i=t(36578),o=t.n(i),a=t(3159),s=t.n(a),u=(0,r.default)(s()).withConfig({displayName:"form-page__StyledFormExample",componentId:"sc-rfrcq8-0"})([".bottom{display:flex;gap:",";}.zero-left{margin-left:0;}.zero-right{margin-right:0;}"],(function(e){return e.theme.spacing.four})),l=(0,r.default)(o()).withConfig({displayName:"form-page__StyledBanner",componentId:"sc-rfrcq8-1"})(["margin-bottom:1rem;"])},3971:function(e,n,t){"use strict";t.r(n);var r=t(59499),i=t(76687),o=t(57061),a=t(3159),s=t.n(a),u=t(67294),l=t(5801),c=t.n(l),d=t(82175),p=t(90878),f=t.n(p),m=t(24777),g=t.n(m),h=t(30038),_=t.n(h),v=t(74231),y=t(57539),x=t.n(y),j=t(68253),w=t(56921),b=t(84506),C=t(89924),S=t(11163),I=t(88916),M=t.n(I),N=t(85893),k=x();n.default=function(){var e=(0,j.Gg)(),n=(0,S.useRouter)().push,t=(0,u.useState)(!1),a=t[0],l=t[1],p=(0,u.useState)(),m=p[0],h=p[1],y=(0,u.useState)([]),x=y[0],I=y[1],z=(0,u.useState)({column:"",id:-1}),P=z[0],A=z[1],B=(0,u.useState)(""),O=B[0],E=B[1],F=(0,u.useState)(!1),G=F[0],D=F[1],U=b;(0,u.useEffect)((function(){if(U.demo){var t={approval_state:1,created_at:"Fri, 22 Jul 2022 16:48:27 GMT",description:"",email:"sitemanager@organization1.com",id:5,name:"John",organization:"NVIDIA",organization_id:1,password_hash:"pbkdf2:sha256:260000$93Zo4zK8kvAb6kkA$99038d7da338cdb1bc6227338f178f66cc6d2af3c471460c5b9e6c62d62c4e07",role:"org_admin",role_id:1,sites:[{name:"site-1",id:0,org:"NVIDIA",num_of_gpus:4,approval_state:100,mem_per_gpu_in_GiB:40},{name:"site-2",id:1,org:"NVIDIA",num_of_gpus:2,approval_state:0,mem_per_gpu_in_GiB:16}],updated_at:"Fri, 22 Jul 2022 16:48:27 GMT"};h((function(){return t}))}else C.y.getUser(e.user.id).then((function(e){e&&h(e.user);var n=e.user.organization;C.y.getClients().then((function(e){var t=e.client_list.filter((function(e){return""!==n&&e.organization===n})).map((function(e){var n,t;return{name:e.name,id:e.id,org:e.organization,num_of_gpus:null===(n=e.capacity)||void 0===n?void 0:n.num_of_gpus,mem_per_gpu_in_GiB:null===(t=e.capacity)||void 0===t?void 0:t.mem_per_gpu_in_GiB,approval_state:e.approval_state}}));I(t)})).catch((function(){}))})).catch((function(e){console.log(e),n("/")}))}),[n,e.user.id,e.user.token,U.demo]);var K=function(e){!function(e,n,t,r){var i=x.map((function(e){return e.id===n?(e[t]=r,e):e}));I(i)}(0,parseInt(e.target.id),e.target.title,O),G?(L(O),D(!1)):V(parseInt(e.target.id),e.target.title,O),E("")},L=function(e){var t={name:e,organization:"undefined"==typeof m?"":m.organization,capacity:{num_of_gpus:4,mem_per_gpu_in_GiB:16}};C.y.postClient(t).then((function(e){if("ok"==e.status){var n=x.map((function(n){return-1==n.id&&(console.log(n),n.id=e.client.id),n}));I(n)}})).catch((function(e){console.log(e),n("/")}))},T=function(e,n){if("ok"==n.status){var t=x.map((function(t){var r,i;t.id==e&&(t={name:n.client.name,id:n.client.id,org:n.client.organization,num_of_gpus:null===(r=n.client.capacity)||void 0===r?void 0:r.num_of_gpus,mem_per_gpu_in_GiB:null===(i=n.client.capacity)||void 0===i?void 0:i.mem_per_gpu_in_GiB,approval_state:n.client.approval_state});return t}));I(t)}},V=function(e,n,t){if("name"===n)C.y.patchClient(e,(0,r.Z)({},n,t)).then((function(n){T(e,n)})).catch((function(e){alert("Error saving site information, you may need to log in again.")}));else if("num_of_gpus"===n){var i,o=null===(i=x.find((function(n){return n.id===e})))||void 0===i?void 0:i.mem_per_gpu_in_GiB;C.y.patchClient(e,{capacity:{num_of_gpus:parseInt(t),mem_per_gpu_in_GiB:o||16}}).then((function(n){T(e,n)})).catch((function(e){alert("Error saving site information, you may need to log in again.")}))}else if("mem_per_gpu_in_GiB"===n){var a,s=null===(a=x.find((function(n){return n.id===e})))||void 0===a?void 0:a.num_of_gpus;C.y.patchClient(e,{capacity:{num_of_gpus:s||0,mem_per_gpu_in_GiB:parseInt(t)}}).then((function(n){T(e,n)})).catch((function(e){alert("Error saving site information, you may need to log in again.")}))}},Z=function(e){A({column:e.target.title,id:-1})},R=(0,u.useCallback)((function(e){e&&e.focus()}),[]),J=[{accessor:"name",Cell:function(e){var n=e.value,t=e.row;return(0,N.jsx)(N.Fragment,{children:"name"==P.column&&P.id==parseInt(t.id)?(0,N.jsx)(N.Fragment,{children:(0,N.jsx)("input",{ref:R,id:t.id,value:O,title:"name",onBlur:function(e){K(e),Z(e)},placeholder:"site name",onChange:function(e){E(e.target.value)}})}):(0,N.jsx)(N.Fragment,{children:(0,N.jsx)("div",{className:"inlineeditlarger",onClick:function(){t.values.approval_state<=0&&(E(n),A({column:"name",id:parseInt(t.id)}))},children:n||"[none]"})})})}},{accessor:"num_of_gpus",Header:"NUM GPUS",Cell:function(e){var n=e.value,t=e.row;return(0,N.jsx)(N.Fragment,{children:"num_of_gpus"==P.column&&P.id==parseInt(t.id)?(0,N.jsx)(N.Fragment,{children:(0,N.jsx)("input",{ref:R,id:t.id,value:O,title:"num_of_gpus",onBlur:function(e){K(e),Z(e)},onChange:function(e){E(e.target.value)}})}):(0,N.jsx)(N.Fragment,{children:(0,N.jsx)("div",{className:"inlineeditlarger",onClick:function(){E(n),A({column:"num_of_gpus",id:parseInt(t.id)})},children:n})})})}},{accessor:"mem_per_gpu_in_GiB",Header:"Memory per gpu (GiB)",Cell:function(e){var n=e.value,t=e.row;return(0,N.jsx)(N.Fragment,{children:"mem_per_gpu_in_GiB"==P.column&&P.id==parseInt(t.id)?(0,N.jsx)(N.Fragment,{children:(0,N.jsx)("input",{ref:R,id:t.id,value:O,title:"mem_per_gpu_in_GiB",onBlur:function(e){K(e),Z(e)},onChange:function(e){E(e.target.value)}})}):(0,N.jsx)(N.Fragment,{children:(0,N.jsx)("div",{className:"inlineeditlarger",onClick:function(){E(n),A({column:"mem_per_gpu_in_GiB",id:parseInt(t.id)})},children:n})})})}},{accessor:"approval_state",Cell:function(e){var n=e.value;e.row;return(0,N.jsx)("div",{className:"inlineeditlarger",children:n<0?"Denied":0==n?"Pending":n>=100?"Approved":n})}},{id:"delete",Cell:function(e){e.v;var n=e.row;return n.values.approval_state<=0?(0,N.jsx)("div",{children:(0,N.jsx)(c(),{icon:{name:"ActionsTrash",variant:"solid"},onClick:function(){C.y.deleteClient(parseInt(n.id)).then((function(e){"ok"==e.status?I(x.filter((function(e){return e.id!=parseInt(n.id)}))):alert(e.status)})).catch((function(e){console.log(e)}))},shape:"rectangle",size:"regular",tag:"button",type:"critical",variant:"outline",width:"fit-content"})}):(0,N.jsx)("div",{children:(0,N.jsx)(c(),{icon:{name:"ActionsTrash",variant:"solid"},disabled:!0,shape:"rectangle",size:"regular",tag:"button",type:"secondary",variant:"outline",width:"fit-content"})})}}];var q=v.Ry().shape({password:v.Z_(),confirm_password:v.Z_().oneOf([v.iH("password")],"Passwords do not match!").when("password",{is:function(e){return"undefined"!=typeof e&&e.length>0},then:v.Z_().required("Passwords do not match!").oneOf([v.iH("password")],"Passwords do not match!")})});return(0,N.jsx)(o.Z,{title:"User Dashboard",children:m?(0,N.jsxs)(N.Fragment,{children:[(0,N.jsxs)("div",{style:{width:"52rem"},children:[m.approval_state<100&&(0,N.jsxs)(w.P,{status:"warning",rounded:!0,children:["Your registration is awaiting approval by the Project Admin. Once approved, you will be able to download your Flare Console","org_admin"==m.role&&" and Client Site Startup Kits"," from the Downloads page."]}),(0,N.jsxs)(s(),{title:m.name,actions:(0,N.jsx)(c(),{type:"primary",variant:"outline",onClick:function(){l(!0)},children:"Edit My Profile"}),children:[(0,N.jsx)("div",{style:{fontSize:"1rem"},children:m.email}),(0,N.jsxs)("div",{style:{fontSize:"1rem",marginTop:".25rem"},children:["Organization: ",m.organization]}),(0,N.jsxs)("div",{style:{fontSize:"1rem",marginTop:".25rem",marginBottom:".5rem"},children:["Role: ","org_admin"==m.role?"Org Admin":"member"==m.role?"Member":"lead"==m.role?"Lead":m.role]})]}),3==e.user.role&&(0,N.jsx)(s(),{actions:(0,N.jsx)(c(),{type:"primary",variant:"outline",onClick:function(){I([].concat((0,i.Z)(x),[{name:"",id:-1,org:"undefined"==typeof m?"":m.organization,num_of_gpus:4,mem_per_gpu_in_GiB:16,approval_state:0}])),A({column:"name",id:-1}),E(""),D(!0)},children:"Add Site"}),title:"Client Sites",children:(0,N.jsx)(k,{columns:J,data:x,rowOnClick:function(){},disableFilters:!0,disableExport:!0,getRowId:function(e,n){return""+e.id}})})]}),(0,N.jsx)(d.J9,{initialValues:m,onSubmit:function(n,t){""!=n.password&&C.y.patchUser(e.user.id,{password:n.password}).then((function(e){t.setSubmitting(!1)}))},validationSchema:q,children:function(e){return(0,N.jsx)(N.Fragment,{children:(0,N.jsx)(_(),{footer:(0,N.jsxs)(N.Fragment,{children:[(0,N.jsx)(c(),{type:"primary",disabled:!e.dirty||!e.isValid||""==e.values.password,onClick:function(){e.handleSubmit(),l(!1)},children:"Save"}),(0,N.jsx)(c(),{type:"secondary",variant:"outline",onClick:function(){l(!1)},children:"Cancel"})]}),onClose:function(){return l(!1)},onDestructiveButtonClick:function(){},onPrimaryButtonClick:function(){},onSecondaryButtonClick:function(){},size:"large",open:a,title:"Edit user details",closeOnBackdropClick:!1,children:(0,N.jsxs)("div",{children:[(0,N.jsx)(f(),{tag:"label",textStyle:"p1",children:"Please contact the project administrator if you need changes to your name, email, or organization."}),(0,N.jsx)("div",{className:"name",style:{display:"flex"},children:(0,N.jsx)(d.gN,{as:g(),className:"zero-left",disabled:!0,label:"Name",name:"name",pattern:e.errors.name,placeholder:"Please enter your name...",validationMessage:e.errors.name})}),(0,N.jsx)(d.gN,{as:g(),className:"zero-left zero-right",disabled:!0,label:"Email",name:"email",pattern:e.errors.email,placeholder:"",validationMessage:e.errors.email}),(0,N.jsx)(d.gN,{as:g(),className:"zero-left zero-right",disabled:!0,label:"Organization",name:"organization",pattern:e.errors.organization,placeholder:"",validationMessage:e.errors.organization}),(0,N.jsxs)("div",{className:"bottom",style:{display:"flex",width:"50%"},children:[(0,N.jsx)(d.gN,{as:M(),className:"zero-left",disabled:e.isSubmitting,label:"Reset user password to:",name:"password",pattern:e.errors.password,placeholder:"",validationMessage:e.errors.password}),(0,N.jsx)(d.gN,{as:M(),className:"zero-right",disabled:e.isSubmitting,label:"Confirm value to reset password to:",name:"confirm_password",pattern:e.errors.confirm_password,placeholder:"",validationMessage:e.errors.confirm_password})]})]})})})}})]}):(0,N.jsx)("span",{children:"loading..."})})}},68253:function(e,n,t){"use strict";t.d(n,{Gg:function(){return a},KY:function(){return i},a5:function(){return o}});var r={user:{email:"",token:"",id:-1,role:0},status:"unauthenticated"};function i(e,n,t,i,o){var a=arguments.length>5&&void 0!==arguments[5]&&arguments[5];return r={user:{email:e,token:n,id:t,role:i,org:o},expired:a,status:0==i?"unauthenticated":"authenticated"},localStorage.setItem("session",JSON.stringify(r)),r}function o(e){return r={user:{email:r.user.email,token:r.user.token,id:r.user.id,role:e,org:r.user.org},expired:r.expired,status:r.status},localStorage.setItem("session",JSON.stringify(r)),r}function a(){var e=localStorage.getItem("session");return null!=e&&(r=JSON.parse(e)),r}},49834:function(e,n,t){(window.__NEXT_P=window.__NEXT_P||[]).push(["/user-dashboard",function(){return t(3971)}])},50029:function(e,n,t){"use strict";function r(e,n,t,r,i,o,a){try{var s=e[o](a),u=s.value}catch(l){return void t(l)}s.done?n(u):Promise.resolve(u).then(r,i)}function i(e){return function(){var n=this,t=arguments;return new Promise((function(i,o){var a=e.apply(n,t);function s(e){r(a,i,o,s,u,"next",e)}function u(e){r(a,i,o,s,u,"throw",e)}s(void 0)}))}}t.d(n,{Z:function(){return i}})},76687:function(e,n,t){"use strict";function r(e,n){(null==n||n>e.length)&&(n=e.length);for(var t=0,r=new Array(n);t<n;t++)r[t]=e[t];return r}function i(e){return function(e){if(Array.isArray(e))return r(e)}(e)||function(e){if("undefined"!==typeof Symbol&&null!=e[Symbol.iterator]||null!=e["@@iterator"])return Array.from(e)}(e)||function(e,n){if(e){if("string"===typeof e)return r(e,n);var t=Object.prototype.toString.call(e).slice(8,-1);return"Object"===t&&e.constructor&&(t=e.constructor.name),"Map"===t||"Set"===t?Array.from(e):"Arguments"===t||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t)?r(e,n):void 0}}(e)||function(){throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}()}t.d(n,{Z:function(){return i}})},84506:function(e){"use strict";e.exports=JSON.parse('{"projectname":"New FL Project","demo":false,"url_root":"http://127.0.0.1:443","arraydata":[{"name":"itemone"},{"name":"itemtwo"},{"name":"itemthree"}]}')}},function(e){e.O(0,[443,539,27,774,888,179],(function(){return n=49834,e(e.s=n);var n}));var n=e.O();_N_E=n}]);