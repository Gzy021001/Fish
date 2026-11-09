<template>
  <div class="h-screen flex overflow-hidden bg-dunhuang-bg font-sans">
    <!-- 移动端侧边栏遮罩 -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 bg-black/40 z-30 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <!-- 侧边栏（小屏为抽屉） -->
    <aside
      class="w-60 shrink-0 flex flex-col z-40 fixed inset-y-0 left-0 transition-transform duration-300 lg:static lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      style="
        background: linear-gradient(
          180deg,
          #82644a 0%,
          #947660 50%,
          #82644a 100%
        );
      "
    >
      <!-- 标题区 -->
      <div class="h-20 flex items-center justify-center gap-2.5 px-4">
        <svg
          class="size-[1.125rem] text-[#f0e0b5]/30 shrink-0"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 12c0-6 8-9 13-5"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 12c0 6 8 9 13 5"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 8l-2.5-4m0 0l-1.5 2"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 16l-2.5 4m0 0l-1.5-2"
          />
          <circle cx="16" cy="10.5" r="1.2" fill="currentColor" stroke="none" />
        </svg>
        <h1
          class="text-sm font-serif font-bold tracking-[0.2em] text-[#f0e0b5]"
        >
          鱼价管理平台
        </h1>
      </div>

      <!-- 分隔 -->
      <div class="mx-6 border-t border-[#f0e0b5]/10"></div>

      <!-- 导航 -->
      <nav class="flex-1 px-3 py-4 space-y-0.5">
        <router-link
          to="/dashboard"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#cfc3a5] transition-all duration-300 hover:text-[#f0e0b5] hover:bg-white/5"
          active-class="!text-[#f0e0b5] !bg-white/10 shadow-[inset_3px_0_0_#c89b6c]"
        >
          <svg
            class="w-4 h-4 shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          {{ t("common.dashboard") }}
        </router-link>

        <router-link
          to="/billing"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#cfc3a5] transition-all duration-300 hover:text-[#f0e0b5] hover:bg-white/5"
          active-class="!text-[#f0e0b5] !bg-white/10 shadow-[inset_3px_0_0_#c89b6c]"
        >
          <svg
            class="w-4 h-4 shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
            />
          </svg>
          {{ t("common.billing") }}
        </router-link>

        <router-link
          to="/species"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-[#cfc3a5] transition-all duration-300 hover:text-[#f0e0b5] hover:bg-white/5"
          active-class="!text-[#f0e0b5] !bg-white/10 shadow-[inset_3px_0_0_#c89b6c]"
        >
          <svg
            class="w-4 h-4 shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
            />
          </svg>
          {{ t("common.species") }}
        </router-link>
      </nav>
    </aside>

    <!-- 主内容 -->
    <main class="flex-1 flex flex-col min-w-0">
      <!-- 顶栏 — 禅净简素 -->
      <header
        class="h-14 lg:h-20 flex items-center justify-between px-3 sm:px-4 lg:px-6 border-b border-[#f0e0b5]/12 shrink-0"
        style="background: linear-gradient(180deg, #947660 0%, #82644a 100%)"
      >
        <div class="flex items-center gap-2 min-w-0">
          <button
            class="lg:hidden p-2 -ml-1 rounded-lg text-[#f0e0b5] hover:bg-white/10 active:scale-95 transition-all"
            aria-label="打开菜单"
            @click="sidebarOpen = !sidebarOpen"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          <h2
            class="text-sm sm:text-base font-serif font-bold tracking-[0.15em] text-[#f0e0b5] truncate"
          >
            {{ routeName }}
          </h2>
        </div>

        <div class="flex items-center gap-2 sm:gap-4 shrink-0">
          <input
            ref="avatarInputRef"
            type="file"
            accept="image/*"
            class="hidden"
            @change="handleAvatarChange"
          />

          <div
            @click="triggerAvatarUpload"
            class="w-8 h-8 rounded-full cursor-pointer transition-all duration-300 hover:opacity-80 overflow-hidden border border-[#f0e0b5]/25"
            :class="avatarUrl ? '' : 'bg-white/10'"
            :title="avatarUrl ? '点击更换头像' : '点击上传头像'"
          >
            <img
              v-if="avatarUrl"
              :src="avatarUrl"
              class="w-full h-full object-cover"
              alt="用户头像"
            />
            <svg
              v-else
              class="w-full h-full p-1.5 text-[#f0e0b5]/60"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
              />
            </svg>
          </div>

          <button
            @click="handleLogout"
            class="inline-flex items-center gap-1.5 px-2.5 sm:px-4 py-1.5 rounded-full text-sm text-[#f5e6c8] bg-[#c89b6c]/15 hover:bg-[#c89b6c]/30 active:scale-95 transition-all duration-300"
          >
            <svg
              class="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
            <span class="hidden sm:inline">退出登录</span>
          </button>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="flex-1 p-3 sm:p-4 lg:p-6 overflow-auto custom-scrollbar">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { compressImage } from "../lib/utils";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

/** 小屏侧边栏抽屉开关 */
const sidebarOpen = ref(false);
watch(
  () => route.fullPath,
  () => {
    sidebarOpen.value = false;
  }
);

const avatarInputRef = ref<HTMLInputElement | null>(null);
const avatarUrl = ref<string | null>(localStorage.getItem("user_avatar"));

const triggerAvatarUpload = () => {
  avatarInputRef.value?.click();
};

const handleAvatarChange = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    // 头像压缩后再进 localStorage，避免大图挤爆 5MB 配额
    let target: File | Blob = file;
    if (file.size > 512 * 1024) {
      target = await compressImage(file, 256, 256, 0.8);
    }
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      avatarUrl.value = dataUrl;
      try {
        localStorage.setItem("user_avatar", dataUrl);
      } catch {
        // 存储满时静默降级：只展示本次会话内的头像
      }
    };
    reader.readAsDataURL(target);
  } catch {
    // 压缩失败时退回原图
    const reader = new FileReader();
    reader.onload = () => {
      avatarUrl.value = reader.result as string;
    };
    reader.readAsDataURL(file);
  }
  input.value = "";
};

const routeName = computed(() => {
  const map: Record<string, string> = {
    Dashboard: t("common.dashboard"),
    Billing: t("common.billing"),
    Import: "批量导入",
    Species: t("common.species"),
    SpeciesDetail: "品种详情",
  };
  return map[route.name as string] || "";
});

const handleLogout = () => {
  authStore.logout();
  router.push("/login");
};
</script>

<style>
@import "../assets/transitions.css";
</style>
