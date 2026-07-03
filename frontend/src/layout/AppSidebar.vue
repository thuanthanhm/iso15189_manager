<script setup>
import { ref, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import AppMenu from './AppMenu.vue';
import api from '@/service/api';

const route = useRoute();
const router = useRouter();

// --- 1. DỮ LIỆU MENU HỆ THỐNG GỐC ---
const globalMenu = ref([
    {
        label: 'Bảng Điều Khiển Tổng',
        items: [
            { label: 'Trang chủ hệ thống', icon: 'pi pi-fw pi-home', to: '/' },
            { label: 'Tài liệu khoa GPB', icon: 'pi pi-fw pi-file-edit', to: '/documents' },
            { label: 'Quản lý hồ sơ', icon: 'pi pi-fw pi-folder-open', to: '/records' }
        ]
    }
]);

// --- 2. ĐỊNH TUYẾN NGỮ CẢNH ---
const isDocumentModule = computed(() => route.path && route.path.startsWith('/documents'));
const isDocumentDetail = computed(() => isDocumentModule.value && route.params.id != null);

// --- 3. QUẢN LÝ CÂY THƯ MỤC TÀI LIỆU ---
const folderTree = ref([]);
const selectedFolderKey = ref(null);
const displayFolderDialog = ref(false);
const displayRenameDialog = ref(false);
const isCreatingSubFolder = ref(false);
const folderForm = ref({ name: '', parent_id: null });
const renameForm = ref({ name: '' });

const fetchFolders = async () => {
    try {
        const response = await api.get('/documents/folders');
        folderTree.value = formatTreeData(response.data);
    } catch (error) { 
        console.error('Lỗi tải cấu trúc thư mục QMS:', error); 
    }
};

const formatTreeData = (nodes) => {
    return nodes.map(node => ({
        key: node.id.toString(),
        label: node.name,
        icon: 'pi pi-fw pi-folder',
        children: node.children && node.children.length ? formatTreeData(node.children) : []
    }));
};

const onNodeSelect = (node) => {
    router.push({ path: '/documents', query: { folder_id: node.key } });
};

const openNewFolderDialog = (isSub) => {
    isCreatingSubFolder.value = isSub;
    if (isSub && selectedFolderKey.value) {
        const parentId = parseInt(Object.keys(selectedFolderKey.value)[0]);
        folderForm.value = { name: '', parent_id: parentId };
    } else {
        folderForm.value = { name: '', parent_id: null };
    }
    displayFolderDialog.value = true;
};

const saveFolder = async () => {
    try {
        await api.post('/documents/folders', folderForm.value);
        displayFolderDialog.value = false;
        fetchFolders(); 
    } catch (error) { 
        alert(error.response?.data?.detail || 'Lỗi tạo thư mục'); 
    }
};

const folderActionItems = computed(() => [
    {
        label: 'Đổi tên thư mục',
        icon: 'pi pi-pencil',
        command: () => {
            if (!selectedFolderKey.value) return; 
            const activeId = Object.keys(selectedFolderKey.value)[0];
            let currentName = 'Thư mục đang chọn';
            const findName = (nodes) => {
                for (let n of nodes) {
                    if (n.key === activeId) currentName = n.label;
                    if (n.children) findName(n.children);
                }
            };
            findName(folderTree.value);
            renameForm.value.name = currentName;
            displayRenameDialog.value = true;
        }
    },
    { separator: true },
    {
        label: 'Xóa thư mục (Admin)',
        icon: 'pi pi-trash',
        command: () => confirmDeleteFolder()
    }
]);

const submitRenameFolder = async () => {
    if (!selectedFolderKey.value) return;
    const folderId = Object.keys(selectedFolderKey.value)[0];
    try {
        await api.put(`/documents/folders/${folderId}`, { name: renameForm.value.name, parent_id: null });
        displayRenameDialog.value = false;
        fetchFolders();
    } catch (error) { 
        alert(error.response?.data?.detail || 'Lỗi khi đổi tên thư mục'); 
    }
};

const confirmDeleteFolder = async () => {
    if (!selectedFolderKey.value) return;
    const folderId = Object.keys(selectedFolderKey.value)[0];
    const isConfirm = confirm(`Bạn có chắc chắn muốn xóa thư mục này?\nCảnh báo: Toàn bộ thư mục con và liên kết bên trong sẽ bị xóa vĩnh viễn!`);
    if (isConfirm) {
        try {
            await api.delete(`/documents/folders/${folderId}`);
            selectedFolderKey.value = null; 
            router.push('/documents'); 
            fetchFolders();
        } catch (error) { 
            alert(error.response?.data?.detail || 'Lỗi khi thực hiện xóa thư mục'); 
        }
    }
};

// --- 4. DANH SÁCH NGỮ CẢNH TÀI LIỆU CÙNG THƯ MỤC ---
const contextualDocs = ref([]);
const isLoadingDocs = ref(false);

const loadContextualDocuments = async (folderId) => {
    if (!folderId) return;
    isLoadingDocs.value = true;
    try {
        const response = await api.get(`/documents/folder/${folderId}`);
        contextualDocs.value = response.data;
    } catch (error) {
        console.error('Lỗi tải tài liệu liên đới:', error);
    } finally {
        isLoadingDocs.value = false;
    }
};

const navigateToDoc = (docId) => {
    router.push({ path: `/documents/${docId}`, query: { folder_id: route.query.folder_id } });
};

// --- 5. TRIGGER API AN TOÀN ---
watch(() => route.path, (newPath) => {
    if (newPath && newPath.startsWith('/documents') && folderTree.value.length === 0) {
        fetchFolders();
    }
}, { immediate: true });

watch(() => route.query.folder_id, (newFolderId) => {
    if (newFolderId) {
        selectedFolderKey.value = { [newFolderId]: true };
        if (isDocumentDetail.value) {
            loadContextualDocuments(newFolderId);
        }
    } else {
        selectedFolderKey.value = null;
    }
}, { immediate: true });

</script>

<template>
    <div class="layout-sidebar">

        <div class="flex flex-column h-full w-full min-h-0">
            
            <div v-if="!isDocumentModule" class="layout-menu-container flex-1 overflow-y-auto">
                <app-menu :model="globalMenu" class="menu-with-guide-lines"></app-menu>
            </div>

            <div v-else-if="isDocumentModule && !isDocumentDetail" class="module-sidebar-wrapper flex-1 flex flex-column min-h-0">
                <div class="sidebar-meta-zone flex-shrink-0 p-3 pb-0">
                    <div class="flex justify-content-between align-items-center mb-3">
                        <span class="font-bold text-primary text-xl white-space-nowrap">Kho & Thư mục</span>
                        <Button icon="pi pi-folder-plus" class="p-button-rounded p-button-text p-button-sm flex-shrink-0" title="Tạo thư mục gốc" @click="openNewFolderDialog(false)" />
                    </div>
                    <div class="flex gap-2 mb-2" v-if="selectedFolderKey && Object.keys(selectedFolderKey).length > 0">
                        <SplitButton label="Thêm thư mục con" icon="pi pi-plus" 
                                     @click="openNewFolderDialog(true)" 
                                     :model="folderActionItems" 
                                     class="p-button-sm w-full p-button-outlined p-button-secondary custom-split-btn" />
                    </div>
                </div>
                
                <div class="sidebar-tree-zone flex-1 overflow-y-auto px-2 pb-2">
                    <Tree :value="folderTree" selectionMode="single" 
                          v-model:selectionKeys="selectedFolderKey" 
                          @node-select="onNodeSelect" 
                          class="border-none bg-transparent p-0 w-full custom-hierarchical-tree"
                          placeholder="Chưa có cấu trúc" />
                </div>
            </div>

            <div v-else-if="isDocumentDetail" class="contextual-sidebar flex-1 flex flex-column min-h-0">
                <div class="flex-shrink-0 p-3 bg-surface-50 border-bottom-1 surface-border">
                    <span class="font-bold text-xs text-secondary text-uppercase tracking-wider block">
                        <i class="pi pi-folder-open mr-2"></i>Tài liệu cùng danh mục
                    </span>
                </div>
                
                <div class="flex-1 overflow-y-auto p-2">
                    <div v-if="isLoadingDocs" class="flex justify-content-center p-4 text-surface-500">
                        <i class="pi pi-spin pi-spinner text-2xl"></i>
                    </div>
                    
                    <ul v-else class="layout-menu m-0 p-0 list-none">
                        <li v-for="doc in contextualDocs" :key="doc.id" 
                            :class="['layout-menuitem-root-text cursor-pointer p-2 border-round transition-colors transition-duration-150 mb-1 border-left-3', 
                                     doc.id == route.params.id ? 'active-route bg-primary-50 text-primary border-primary' : 'border-transparent hover:bg-surface-100']"
                            @click="navigateToDoc(doc.id)">
                            <a class="flex flex-column gap-1 text-color no-underline w-full p-1">
                                <span class="font-bold text-sm" :class="doc.id == route.params.id ? 'text-primary' : 'text-primary-600'">{{ doc.code }}</span>
                                <span class="text-xs text-surface-700 font-medium line-clamp-custom" :title="doc.title">
                                    {{ doc.title }}
                                </span>
                            </a>
                        </li>
                    </ul>
                </div>
            </div>

        </div>

    </div>

    <Dialog header="Tạo thư mục mới" v-model:visible="displayFolderDialog" :style="{ width: '25vw' }" :modal="true" class="p-fluid">
        <div class="field">
            <label>Tên thư mục</label>
            <InputText v-model="folderForm.name" autofocus @keyup.enter="saveFolder" />
        </div>
        <template #footer>
            <Button label="Hủy" icon="pi pi-times" @click="displayFolderDialog = false" class="p-button-text" />
            <Button label="Khởi tạo" icon="pi pi-check" @click="saveFolder" />
        </template>
    </Dialog>

    <Dialog header="Đổi tên thư mục" v-model:visible="displayRenameDialog" :style="{ width: '25vw' }" :modal="true" class="p-fluid">
        <div class="field">
            <label>Tên thư mục mới</label>
            <InputText v-model="renameForm.name" autofocus @keyup.enter="submitRenameFolder" />
        </div>
        <template #footer>
            <Button label="Hủy" icon="pi pi-times" @click="displayRenameDialog = false" class="p-button-text" />
            <Button label="Lưu thay đổi" icon="pi pi-check" @click="submitRenameFolder" />
        </template>
    </Dialog>
</template>

<style scoped>
/* Đảm bảo custom split button dàn đủ 100% không gian */
:deep(.custom-split-btn) {
    width: 100% !important;
    display: inline-flex;
}
:deep(.custom-split-btn .p-splitbutton-defaultbutton) {
    flex-grow: 1;
    text-align: left;
    justify-content: flex-start;
}

/* Cắt chữ 2 dòng (Bắt buộc 4 thuộc tính để tương thích mọi trình duyệt) */
.line-clamp-custom {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    line-height: 1.4;
}

/* Cấu hình hiển thị Cây thư mục */
:deep(.custom-hierarchical-tree .p-treenode-label) {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.95rem;
}
:deep(.custom-hierarchical-tree .p-treenode-children) {
    padding-left: 1.2rem !important;
    margin-left: 0.6rem !important;
    border-left: 1px dashed var(--surface-400, #b4c2d3) !important; 
}
:deep(.custom-hierarchical-tree > .p-treenode-children) {
    border-left: none !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
}
:deep(.custom-hierarchical-tree .p-treenode-content) {
    border-radius: 6px;
    margin-bottom: 0.2rem;
    padding: 0.3rem 0.5rem;
    transition: background-color 0.15s;
}
:deep(.custom-hierarchical-tree .p-treenode-content.p-highlight) {
    background-color: var(--primary-50) !important;
    color: var(--primary-color) !important;
    font-weight: 600;
}
</style>