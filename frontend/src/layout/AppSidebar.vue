<script setup>
import { ref, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/service/api';

const route = useRoute();
const router = useRouter();

const folderTree = ref([]);
const folderDocuments = ref([]);
const loadingDocs = ref(false);

// Kiểm tra xem có đang ở màn hình xem chi tiết một quy trình hay không
const isDetailRoute = computed(() => {
    return !!route.params.id;
});

// Lấy ID tài liệu hiện tại đang chọn trên route
const currentDocId = computed(() => {
    return route.params.id ? Number(route.params.id) : null;
});

// Tải cây thư mục (Dùng khi ở màn hình tổng)
const loadFolderTree = async () => {
    try {
        const response = await api.get('/documents/folders');
        folderTree.value = response.data;
    } catch (error) {
        console.error('Lỗi nạp cây thư mục:', error);
    }
};

// Tải danh sách tài liệu cùng thư mục (Dùng làm điều hướng ngữ cảnh)
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

// Điều hướng nhanh khi nhân sự click đổi tài liệu trên Sidebar ngữ cảnh
const navigateToDocument = (docId) => {
    router.push({
        path: `/documents/${docId}`,
        query: { folder_id: route.query.folder_id }
    });
};

// Theo dõi sự biến động của Route để chuyển đổi dữ liệu hiển thị song song
watch(
    () => route.query.folder_id,
    (newFolderId) => {
        if (newFolderId) {
            loadFolderDocuments(newFolderId);
        }
    },
    { immediate: true }
);

onMounted(() => {
    loadFolderTree();
});
</script>

<template>
    <div class="layout-sidebar-wrapper h-full flex flex-column">
        
        <div v-if="!isDetailRoute" class="tree-menu-container p-3 flex-1 overflow-y-auto">
            <div class="sidebar-header mb-3">
                <span class="text-xs font-bold text-muted text-uppercase tracking-wider"><i class="pi pi-box mr-2"></i>Kho & Thư mục ISO</span>
            </div>
            
            <div class="folder-tree-mock">
                <div v-for="folder in folderTree" :key="folder.id" class="p-2 hover:surface-100 border-round cursor-pointer text-sm font-medium mb-1">
                    <i class="pi pi-folder text-yellow-500 mr-2"></i>{{ folder.name }}
                </div>
            </div>
        </div>

        <div v-else class="contextual-menu-container flex flex-column h-full">
            <div class="p-3 bg-surface-50 border-bottom-1 surface-border flex align-items-center justify-content-between">
                <span class="font-bold text-xs text-secondary text-uppercase tracking-wider"><i class="pi pi-folder-open mr-2"></i>Tài liệu cùng danh mục</span>
                <i v-if="loadingDocs" class="pi pi-spin pi-spinner text-primary text-xs"></i>
            </div>

            <div class="flex-1 overflow-y-auto p-2 layout-context-scroll">
                <div v-for="doc in folderDocuments" :key="doc.id" 
                     @click="navigateToDocument(doc.id)"
                     :class="['context-doc-node p-2.5 border-round cursor-pointer mb-2 flex flex-column gap-1 transition-colors transition-duration-150', 
                              doc.id === currentDocId ? 'active-context-node shadow-1' : 'hover:bg-surface-100']">
                    <div class="flex align-items-center justify-content-between">
                        <span class="font-bold text-xs text-primary-600">{{ doc.code }}</span>
                        <span class="text-xs text-muted font-semibold">v1.0</span>
                    </div>
                    <span class="text-xs text-surface-700 font-medium text-ellipse">{{ doc.title }}</span>
                </div>
                
                <div v-if="folderDocuments.length === 0 && !loadingDocs" class="p-3 text-center text-muted text-xs">
                    Không có tài liệu nào khác.
                </div>
            </div>
        </div>

    </div>
</template>

<style scoped>
.layout-sidebar-wrapper {
    background-color: var(--surface-card);
}
.layout-context-scroll::-webkit-scrollbar {
    width: 5px;
}
.layout-context-scroll::-webkit-scrollbar-thumb {
    background: var(--surface-300);
    border-radius: 3px;
}
.context-doc-node {
    border: 1px solid transparent;
}
.active-context-node {
    background-color: var(--primary-50) !important;
    border-left: 4px solid var(--primary-color) !important;
    border-color: var(--primary-100) !important;
}
.text-ellipse {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.4;
}
</style>