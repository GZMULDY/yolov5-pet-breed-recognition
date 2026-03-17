<template>
  <!-- 路由视图 - 显示当前路由对应的页面组件 -->
  <router-view />
  <!-- 全局自定义提示弹窗 -->
  <CustomToast
    :visible="toastState.visible"
    :title="toastState.title"
    :message="toastState.message"
    :type="toastState.type"
    :duration="toastState.duration"
    @close="hideToast"
  />
</template>

<script setup>
import CustomToast from './components/CustomToast.vue';
import { useToast, toastState, hideToast } from './composables/useToast';
</script>

<script>
/**
 * App 根组件
 * 所有页面的父组件，用于全局配置和状态管理
 */
export default {
  name: 'App'
}
</script>

<style>
/**
 * 全局样式
 * 作用于所有页面
 */

/* 基础重置 - 移除默认 margin 和 padding */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* 页面基础样式 */
page {
  /* 统一为粉色背景 */
  background-color: #fff5f7;
  /* 文字颜色 */
  color: #2d3436;
  /* 字体设置 */
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif;
}

/* 隐藏滚动条 - 提升移动端体验 */
::-webkit-scrollbar {
  display: none;
  width: 0 !important;
  height: 0 !important;
  -webkit-appearance: none;
  background: transparent;
}
</style>