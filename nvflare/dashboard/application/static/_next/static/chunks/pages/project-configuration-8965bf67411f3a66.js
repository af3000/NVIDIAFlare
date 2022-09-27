(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[800],{89924:function(e,t,n){"use strict";n.d(t,{y:function(){return j}});var r=n(9669),i=n.n(r),o=n(84506),s=n(68253),a=n(35823),c=n.n(a),l=o,u=i().create({baseURL:l.url_root+"/api/v1/",headers:{"Access-Control-Allow-Origin":"*"}});u.interceptors.request.use((function(e){return e.headers.Authorization="Bearer "+(0,s.Gg)().user.token,e}),(function(e){console.log("Interceptor request error: "+e)})),u.interceptors.response.use((function(e){return e}),(function(e){throw console.log(" AXIOS error: "),console.log(e),401===e.response.status&&(0,s.KY)("","",-1,0,"",!0),403===e.response.status&&console.log("Error: "+e.response.data.status),409===e.response.status&&console.log("Error: "+e.response.data.status),422===e.response.status&&(0,s.KY)("","",-1,0,"",!0),e}));var d=function(e){return e.data},p=function(e){return u.get(e).then(d)},f=function(e,t,n){return u.post(e,{pin:n},{responseType:"blob"}).then((function(e){t=e.headers["content-disposition"].split('"')[1],c()(e.data,t)}))},h=function(e,t){return u.post(e,t).then(d)},g=function(e,t){return u.patch(e,t).then(d)},m=function(e){return u.delete(e).then(d)},j={login:function(e){return h("login",e)},getUsers:function(){return p("users")},getUser:function(e){return p("users/".concat(e))},getUserStartupKit:function(e,t,n){return f("users/".concat(e,"/blob"),t,n)},getClientStartupKit:function(e,t,n){return f("clients/".concat(e,"/blob"),t,n)},getOverseerStartupKit:function(e,t){return f("overseer/blob",e,t)},getServerStartupKit:function(e,t,n){return f("servers/".concat(e,"/blob"),t,n)},getClients:function(){return p("clients")},getProject:function(){return p("project")},postUser:function(e){return h("users",e)},patchUser:function(e,t){return g("users/".concat(e),t)},deleteUser:function(e){return m("users/".concat(e))},postClient:function(e){return h("clients",e)},patchClient:function(e,t){return g("clients/".concat(e),t)},deleteClient:function(e){return m("clients/".concat(e))},patchProject:function(e){return g("project",e)},getServer:function(){return p("server")},patchServer:function(e){return g("server",e)}}},57061:function(e,t,n){"use strict";n.d(t,{Z:function(){return N}});var r=n(50029),i=n(87794),o=n.n(i),s=n(41664),a=n.n(s),c=n(29224),l=n.n(c),u=n(70491),d=n.n(u),p=n(86188),f=n.n(p),h=n(31096),g=h.default.div.withConfig({displayName:"styles__StyledLayout",componentId:"sc-xczy9u-0"})(["overflow:hidden;height:100%;width:100%;margin:0;padding:0;display:flex;flex-wrap:wrap;.menu{height:auto;}.content-header{flex:0 0 80px;}"]),m=h.default.div.withConfig({displayName:"styles__StyledContent",componentId:"sc-xczy9u-1"})(["display:flex;flex-direction:column;flex:1 1 0%;overflow:auto;height:calc(100% - 3rem);.inlineeditlarger{padding:10px;}.inlineedit{padding:10px;margin:-10px;}.content-wrapper{padding:",";min-height:800px;}"],(function(e){return e.theme.spacing.four})),j=n(11163),x=n(84506),v=n(67294),b=n(68253),y=n(13258),_=n.n(y),S=n(5801),w=n.n(S),P=n(89924),C=n(85893),N=function(e){var t=e.children,n=e.headerChildren,i=e.title,s=(0,j.useRouter)(),c=s.pathname,u=s.push,h=x,S=(0,v.useState)(),N=S[0],O=S[1],z=(0,b.Gg)();(0,v.useEffect)((function(){P.y.getProject().then((function(e){O(e.project)}))}),[]);var I=function(){var e=(0,r.Z)(o().mark((function e(){return o().wrap((function(e){for(;;)switch(e.prev=e.next){case 0:(0,b.KY)("none","",-1,0),u("/");case 2:case"end":return e.stop()}}),e)})));return function(){return e.apply(this,arguments)}}();return(0,C.jsxs)(g,{children:[(0,C.jsx)(l(),{app:null===N||void 0===N?void 0:N.short_name,appBarActions:z.user.role>0?(0,C.jsxs)("div",{style:{display:"flex",flexDirection:"row",alignItems:"center",marginRight:10},children:[h.demo&&(0,C.jsx)("div",{children:"DEMO MODE"}),(0,C.jsx)(_(),{parentElement:(0,C.jsx)(w(),{icon:{name:"AccountCircleGenericUser",color:"white",size:22},shape:"circle",variant:"link",className:"logout-link"}),position:"top-right",children:(0,C.jsxs)(C.Fragment,{children:[(0,C.jsx)(y.ActionMenuItem,{label:"Logout",onClick:I}),!1]})})]}):(0,C.jsx)(C.Fragment,{})}),(0,C.jsxs)(f(),{className:"menu",itemMatchPattern:function(e){return e===c},itemRenderer:function(e){var t=e.title,n=e.href;return(0,C.jsx)(a(),{href:n,children:t})},location:c,children:[0==z.user.role&&(0,C.jsxs)(p.MenuContent,{children:[(0,C.jsx)(p.MenuItem,{href:"/",icon:{name:"AccountUser"},title:"Login"}),(0,C.jsx)(p.MenuItem,{href:"/registration-form",icon:{name:"ObjectsClipboardEdit"},title:"User Registration Form"})]}),4==z.user.role&&(0,C.jsxs)(p.MenuContent,{children:[(0,C.jsx)(p.MenuItem,{href:"/",icon:{name:"ViewList"},title:"Project Home"}),(0,C.jsx)(p.MenuItem,{href:"/user-dashboard",icon:{name:"ServerEdit"},title:"My Info"}),(0,C.jsx)(p.MenuItem,{href:"/project-admin-dashboard",icon:{name:"AccountGroupShieldAdd"},title:"Users Dashboard"}),(0,C.jsx)(p.MenuItem,{href:"/site-dashboard",icon:{name:"ConnectionNetworkComputers2"},title:"Client Sites"}),(0,C.jsx)(p.MenuItem,{href:"/project-configuration",icon:{name:"SettingsCog"},title:"Project Configuration"}),(0,C.jsx)(p.MenuItem,{href:"/application-config",icon:{name:"WindowModule"},title:"Application Configuration"}),(0,C.jsx)(p.MenuItem,{href:"/server-config",icon:{name:"ConnectionServerNetwork1"},title:"Server Configuration"}),(0,C.jsx)(p.MenuItem,{href:"/downloads",icon:{name:"ActionsDownload"},title:"Downloads"}),(0,C.jsx)(p.MenuItem,{href:"/logout",icon:{name:"PlaybackStop"},title:"Logout"})]}),(1==z.user.role||2==z.user.role||3==z.user.role)&&(0,C.jsxs)(p.MenuContent,{children:[(0,C.jsx)(p.MenuItem,{href:"/",icon:{name:"ViewList"},title:"Project Home Page"}),(0,C.jsx)(p.MenuItem,{href:"/user-dashboard",icon:{name:"ServerEdit"},title:"My Info"}),(0,C.jsx)(p.MenuItem,{href:"/downloads",icon:{name:"ActionsDownload"},title:"Downloads"}),(0,C.jsx)(p.MenuItem,{href:"/logout",icon:{name:"PlaybackStop"},title:"Logout"})]}),(0,C.jsx)(p.MenuFooter,{})]}),(0,C.jsxs)(m,{children:[(0,C.jsx)(d(),{className:"content-header",title:i,children:n}),(0,C.jsx)("div",{className:"content-wrapper",children:t})]})]})}},56921:function(e,t,n){"use strict";n.d(t,{P:function(){return l},X:function(){return c}});var r=n(31096),i=n(36578),o=n.n(i),s=n(3159),a=n.n(s),c=(0,r.default)(a()).withConfig({displayName:"form-page__StyledFormExample",componentId:"sc-rfrcq8-0"})([".bottom{display:flex;gap:",";}.zero-left{margin-left:0;}.zero-right{margin-right:0;}"],(function(e){return e.theme.spacing.four})),l=(0,r.default)(o()).withConfig({displayName:"form-page__StyledBanner",componentId:"sc-rfrcq8-1"})(["margin-bottom:1rem;"])},6052:function(e,t,n){"use strict";n.r(t);var r=n(59499),i=n(82175),o=n(74231),s=n(5801),a=n.n(s),c=n(90878),l=n.n(c),u=n(24777),d=n.n(u),p=n(57061),f=n(56921),h=n(67294),g=n(89924),m=n(11163),j=n(35827),x=n.n(j),v=n(85893);function b(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function y(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?b(Object(n),!0).forEach((function(t){(0,r.Z)(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):b(Object(n)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}var _=o.Ry().shape({short_name:o.Z_(),description:o.Z_(),docker_link:o.Z_()});t.default=function(){var e=(0,m.useRouter)().push,t=(0,h.useState)(""),n=t[0],r=t[1],o=(0,h.useState)(),s=o[0],c=o[1];return(0,h.useEffect)((function(){g.y.getProject().then((function(e){c(e.project)}))}),[]),(0,v.jsx)(v.Fragment,{children:(0,v.jsx)(p.Z,{title:"Project Configuration:",children:s?(0,v.jsx)(i.J9,{initialValues:s,onSubmit:function(t,n){console.log("Submitting values: ".concat(JSON.stringify(t,null,2))),g.y.patchProject({short_name:t.short_name,title:t.title,description:t.description,app_location:t.app_location,starting_date:t.starting_date,end_date:t.end_date,frozen:!1}).then((function(e){c(e.project),n.setSubmitting(!1),n.resetForm({values:e.project})})).catch((function(t){console.log(t),e("/")}))},validationSchema:_,children:function(t){var o,u;return(0,v.jsx)(v.Fragment,{children:(0,v.jsxs)("div",{style:{minHeight:"835px"},children:[t.values.frozen&&(0,v.jsx)(f.P,{status:"warning",rounded:!0,children:"This project has been frozen. Project values are no longer editable."}),(0,v.jsxs)(f.X,{loading:t.isSubmitting,title:"Project Values",children:[(0,v.jsx)(l(),{tag:"label",textStyle:"p1",children:"Set the values for the information of the FL project."}),(0,v.jsx)(i.gN,{as:d(),className:"zero-left zero-right",disabled:t.isSubmitting||t.values.frozen,label:"Project Short Name (maximum 16 characters, at top left, and used in certs)",name:"short_name",pattern:t.errors.short_name,placeholder:"",validationMessage:t.errors.short_name}),(0,v.jsx)(i.gN,{as:d(),className:"zero-left zero-right",disabled:t.isSubmitting||t.values.frozen,label:"Title (on home page)",name:"title",pattern:t.errors.title,placeholder:"Federated learning for predicting clinical outcomes in patients with COVID-19",validationMessage:t.errors.title}),(0,v.jsx)(i.gN,{as:d(),inputType:"multiLine",className:"zero-left zero-right",disabled:t.isSubmitting||t.values.frozen,label:"Project Description",name:"description",pattern:t.errors.description,placeholder:"",validationMessage:t.errors.description}),(0,v.jsxs)("div",{className:"bottom",children:[""===t.values.starting_date||"starting_date"===n?(0,v.jsx)(i.gN,{as:x(),className:"zero-left zero-right",disabled:t.isSubmitting||t.values.frozen,label:"Project Start Date",name:"starting_date",pattern:t.errors.starting_date,starting_date:t.values.starting_date,onChange:function(e){t.setFieldValue("starting_date",e.toUTCString()),r("")}}):(0,v.jsx)(v.Fragment,{children:(0,v.jsxs)("div",{style:{display:"inline-block",width:"240px"},children:[(0,v.jsx)("div",{children:(0,v.jsx)("p",{style:{margin:"0 0 0.25rem"},children:"Project Start Date"})}),(0,v.jsx)("br",{}),(0,v.jsx)("div",{style:{position:"relative",top:"-12px",right:"-16px"},onClick:function(){t.values.frozen||r("starting_date")},children:null===(o=t.values.starting_date)||void 0===o?void 0:o.substring(0,t.values.starting_date.length-13)})]})}),""===t.values.end_date||"end_date"===n?(0,v.jsx)(i.gN,{as:x(),className:"zero-left zero-right",disabled:t.isSubmitting||t.values.frozen,label:"Project End Date",name:"end_date",pattern:t.errors.end_date,onChange:function(e){t.setFieldValue("end_date",e.toUTCString()),r("")}}):(0,v.jsx)(v.Fragment,{children:(0,v.jsxs)("div",{style:{display:"inline-block",width:"240px"},children:[(0,v.jsx)("div",{children:(0,v.jsx)("p",{style:{margin:"0 0 0.25rem"},children:"Project End Date"})}),(0,v.jsx)("br",{}),(0,v.jsx)("div",{style:{position:"relative",top:"-12px",right:"-16px"},onClick:function(){t.values.frozen||r("end_date")},children:null===(u=t.values.end_date)||void 0===u?void 0:u.substring(0,t.values.end_date.length-13)})]})}),t.values.public?(0,v.jsx)(a(),{disabled:!0,onClick:function(){g.y.patchProject({public:!1}).then((function(e){c(e.project)})).catch((function(t){console.log(t),e("/")})),t.values.public=!1,c(y(y({},s),{},{public:!1}))},children:"Project is Public"}):(0,v.jsx)(a(),{onClick:function(){g.y.patchProject({public:!0}).then((function(e){c(e.project)})).catch((function(t){console.log(t),e("/")})),t.values.public=!0,c(y(y({},s),{},{public:!0}))},children:"Make Project Public"}),(0,v.jsx)("div",{style:{marginTop:"18px"},children:"If the project is public, user signup is enabled."})]}),(0,v.jsx)("br",{}),(0,v.jsx)(a(),{disabled:!t.dirty||!t.isValid||t.values.frozen,onClick:function(){return t.handleSubmit()},children:"Save"}),(0,v.jsx)("br",{}),!t.values.frozen&&(0,v.jsx)(f.P,{status:"info",rounded:!0,children:"After setting all the values for the project configuartion, application, and server configuration, click Freeze Project on the Project Home page to freeze all the values and allow downloads of the project artifacts."})]})]})})}}):(0,v.jsx)("span",{children:"loading..."})})})}},68253:function(e,t,n){"use strict";n.d(t,{Gg:function(){return s},KY:function(){return i},a5:function(){return o}});var r={user:{email:"",token:"",id:-1,role:0},status:"unauthenticated"};function i(e,t,n,i,o){var s=arguments.length>5&&void 0!==arguments[5]&&arguments[5];return r={user:{email:e,token:t,id:n,role:i,org:o},expired:s,status:0==i?"unauthenticated":"authenticated"},localStorage.setItem("session",JSON.stringify(r)),r}function o(e){return r={user:{email:r.user.email,token:r.user.token,id:r.user.id,role:e,org:r.user.org},expired:r.expired,status:r.status},localStorage.setItem("session",JSON.stringify(r)),r}function s(){var e=localStorage.getItem("session");return null!=e&&(r=JSON.parse(e)),r}},71068:function(e,t,n){(window.__NEXT_P=window.__NEXT_P||[]).push(["/project-configuration",function(){return n(6052)}])},84506:function(e){"use strict";e.exports=JSON.parse('{"projectname":"New FL Project","demo":false,"url_root":"http://127.0.0.1:443","arraydata":[{"name":"itemone"},{"name":"itemtwo"},{"name":"itemthree"}]}')}},function(e){e.O(0,[443,27,403,774,888,179],(function(){return t=71068,e(e.s=t);var t}));var t=e.O();_N_E=t}]);