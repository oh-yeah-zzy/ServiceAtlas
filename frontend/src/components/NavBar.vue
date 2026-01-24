<template>
  <nav class="navbar">
    <div class="nav-brand">
      <router-link to="/">ServiceAtlas</router-link>
    </div>
    <ul class="nav-links">
      <li>
        <router-link to="/" :class="{ active: $route.path === '/' }">
          {{ $t('common.dashboard') }}
        </router-link>
      </li>
      <li>
        <router-link to="/services" :class="{ active: $route.path === '/services' }">
          {{ $t('common.services') }}
        </router-link>
      </li>
      <li>
        <router-link to="/topology" :class="{ active: $route.path === '/topology' }">
          {{ $t('common.topology') }}
        </router-link>
      </li>
      <li>
        <a :href="docsUrl" target="_blank">{{ $t('common.apiDocs') }}</a>
      </li>
    </ul>
    <div class="nav-actions">
      <LanguageSwitcher />
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import LanguageSwitcher from './LanguageSwitcher.vue'
import { getBasePath } from '@/utils/basePath'

const docsUrl = computed(() => {
  const basePath = getBasePath()
  return `${basePath}/docs`
})
</script>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1.25rem 2.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
  position: sticky;
  top: 0;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.nav-brand a {
  color: white;
  font-size: 1.75rem;
  font-weight: 800;
  text-decoration: none;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  transition: all 0.3s;
}

.nav-brand a:hover {
  transform: scale(1.05);
  text-shadow: 0 4px 20px rgba(255, 255, 255, 0.3);
}

.nav-links {
  display: flex;
  list-style: none;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
}

.nav-links a {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  padding: 0.625rem 1.25rem;
  border-radius: 10px;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 0.95rem;
  position: relative;
  display: inline-block;
}

.nav-links a::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  transform: scaleY(0);
  transform-origin: bottom;
  transition: transform 0.3s ease;
  z-index: -1;
}

.nav-links a:hover::before {
  transform: scaleY(1);
}

.nav-links a:hover {
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.nav-links a.active {
  color: white;
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  font-weight: 600;
}

.nav-actions {
  display: flex;
  align-items: center;
}

@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem 1.5rem;
  }

  .nav-links {
    flex-wrap: wrap;
    justify-content: center;
  }

  .nav-brand a {
    font-size: 1.5rem;
  }
}
</style>
