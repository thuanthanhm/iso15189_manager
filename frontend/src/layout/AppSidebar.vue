<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/service/api';
import AppMenu from './AppMenu.vue';

const route = useRoute();
const router = useRouter();

const folderDocuments = ref([]);
const loadingDocs = ref(false);

const isDetailRoute = computed(() => !!route.params.id && route.path.includes('/documents/'));
const currentDocId = computed(() => route.params.id ? Number(route.params.id) : null);

const loadFolderDocuments = async (folderId) => {
    if (!folderId) return;
    loadingDocs.value = true;
    try {
        const response = await api.get(`/documents/folder/${folderId}`);
        folderDocuments.value = response.data;
    } catch (error) {
        console.error('Lỗi tải danh sách ngữ cảnh:', error);
    } finally {
        loadingDocs.value = false;
    }
};

const navigateToDocument = (docId) => {
    router.push({
        path: `/documents/${docId}`,
        query: { folder_id: route.query.folder_id }
    });
};

watch(
    () => route.query.folder_id,
    (newFolderId) => {
        if (newFolderId) {
            loadFolderDocuments(newFolderId);
        }
    },
    { immediate: true }
);
</script>

<template>
    <div class="layout-sidebar-wrapper">
        <AppMenu v-if="!isDetailRoute" />

        <div v-else class="context-menu-container">
            <ul class="layout-menu">
                <li class="layout-root-menuitem">
                    <div class="layout-menuitem-root-text">Tài liệu cùng danh mục</div>
                    <a tabindex="-1" style="display: none;"></a>
                    
                    <ul class="layout-submenu">
                        <li v-for="doc in folderDocuments" :key="doc.id" :class="{ 'active-menuitem': doc.id === currentDocId }">
                            <a @click="navigateToDocument(doc.id)" 
                               :class="{ 'active-route': doc.id === currentDocId }" 
                               class="p-ripple" 
                               style="cursor: pointer;">
                                <i class="layout-menuitem-icon pi pi-file-pdf"></i>
                                <span class="layout-menuitem-text text-ellipse" style="line-height: 1.4;">
                                    <span class="font-bold block mb-1 text-sm">{{ doc.code }}</span>
                                    <span class="text-xs">{{ doc.title }}</span>
                                </span>
                            </a>
                        </li>
                        
                        <li v-if="loadingDocs">
                            <span class="layout-menuitem-text text-muted p-3"><i class="pi pi-spin pi-spinner mr-2"></i>Đang tải...</span>
                        </li>
                        <li v-else-if="folderDocuments.length === 0">
                            <span class="layout-menuitem-text text-muted p-3">Không có tài liệu nào khác.</span>
                        </li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</template>

<style scoped>
.text-ellipse {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: normal;
}
</style>