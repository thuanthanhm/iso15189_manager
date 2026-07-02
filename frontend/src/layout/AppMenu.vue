<script setup>
import AppMenuItem from './AppMenuItem.vue';

// Nhận mảng dữ liệu (model) từ file cha truyền xuống
const props = defineProps({
    model: {
        type: Array,
        default: () => []
    }
});
</script>

<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="item.label">
            <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
            <li v-if="item.separator" class="menu-separator"></li>
        </template>
    </ul>
</template>