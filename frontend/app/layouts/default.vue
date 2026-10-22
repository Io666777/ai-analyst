<template>
  <div :class="$style.DefaultLayout">
    <main :class="$style.main">
      <slot />
    </main>
  </div>
</template>

<style lang="scss" module>
.DefaultLayout {
  min-height: 100dvh;
}

.main {
  margin: 0 auto;
  padding: 1.5rem 1rem;
  max-width: 75rem;

  @include respond-to(mobile) {
    padding: 1rem 0.75rem;
  }
}
</style>
