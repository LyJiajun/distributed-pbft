import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'

// 导入页面组件
import HomePage from './views/HomePage.vue'
import NodePage from './views/NodePage.vue'
import JoinPage from './views/JoinPage.vue'

// 路由配置
const routes = [
  { path: '/', component: HomePage },
  { path: '/join/:sessionId', component: JoinPage },
  { path: '/node/:sessionId/:nodeId', component: NodePage }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(router)
app.use(ElementPlus)
app.mount('#app') 