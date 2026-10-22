<template>
  <section :class="$style.IndexPage">
    <h1 :class="$style.title">AI-аналитик для малого бизнеса</h1>
    <p :class="$style.lead">Загрузка файла появится на следующих шагах.</p>
  </section>
</template>

<style lang="scss" module>
.IndexPage {
  display: grid;
  gap: 1rem;
}

.title {
  @include text(h1);
}

.lead {
  color: var(--base-700);
}
</style>
