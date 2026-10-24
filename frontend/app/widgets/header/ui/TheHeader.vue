<template>
  <header :class="$style.TheHeader">
    <div :class="$style.inner">
      <NuxtLink :to="ROUTES.home" :class="$style.logo">AI-аналитик</NuxtLink>

      <nav v-if="session.isPrepared.value" :class="$style.nav" aria-label="Разделы анализа">
        <NuxtLink
          v-for="link in LINKS"
          :key="link.to"
          :to="link.to"
          :class="$style.link"
          :exact-active-class="$style._active"
        >
          {{ link.label }}
        </NuxtLink>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
/**
 * Шапка сайта: название - ссылка на главную, разделы анализа - когда данные размечены.
 * Активный раздел подсвечивается, у ссылки - aria-current="page" (ставит NuxtLink).
 */
import { NuxtLink } from '#components';
import { useSession } from '~/entities/session';
import { ROUTES } from '~/shared/config';

const LINKS = [
  { to: ROUTES.home, label: 'Данные' },
  { to: ROUTES.overview, label: 'Обзор' },
  { to: ROUTES.top, label: 'Топ' },
  { to: ROUTES.item, label: 'Товар' },
] as const;

const session = useSession();
</script>

<style lang="scss" module>
.TheHeader {
  background: var(--white);
  border-bottom: var(--border-width) solid var(--base-100);
}

.inner {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-5);
  align-items: center;
  max-width: 75rem;
  padding: var(--space-3) var(--space-4);
  margin: 0 auto;

  @include respond-to(mobile) {
    padding: var(--space-2) var(--space-3);
  }
}

.logo {
  color: var(--base-900);
  text-decoration: none;

  @include text(h3);
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
}

.link {
  padding: var(--space-1) var(--space-3);
  color: var(--base-700);
  text-decoration: none;
  border-radius: var(--radius-small);
  transition:
    background var(--default-transition),
    color var(--default-transition);

  @include text(small);

  &:hover {
    color: var(--primary-600);
    background: var(--base-100);
  }

  &:focus-visible {
    outline: var(--focus-width) solid var(--primary-500);
    outline-offset: var(--focus-width);
  }

  &._active {
    color: var(--primary-600);
    background: var(--primary-100);
  }
}
</style>
