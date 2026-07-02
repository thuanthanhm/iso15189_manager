<script setup>
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import api from '@/service/api';

// Nhúng cả 2 màn hình con vào
import DocumentEditor from './DocumentEditor.vue';
import DocumentDetail from './DocumentDetail.vue';

const route = useRoute();
const documents = ref([]);
const expandedRows = ref([]);

// Các cờ điều khiển hoán đổi màn hình
const isCreating = ref(false);
const isViewing = ref(false);
const selectedDocId = ref(null);

const searchQuery = ref('');
const docForm = ref({ code: '', title: '', doc_type: 'PDF_INTERNAL', folder_id: null });

const fakeAttachments = [
    { name: 'BM.01 - Phiếu yêu cầu xét nghiệm', type: 'PDF' },
    { name: 'BM.02 - Sổ giao nhận bệnh phẩm', type: 'WORD' }
];

const filteredDocuments = computed(() => {
    if (!searchQuery.value) return documents.value;
    const lowerQuery = searchQuery.value.toLowerCase();
    return documents.value.filter(doc => 
        (doc.code && doc.code.toLowerCase().includes(lowerQuery)) || 
        (doc.title && doc.title.toLowerCase().includes(lowerQuery))
    );
});

const loadDocuments = async (folderId) => {
    try {
        const response = await api.get(`/documents/folder/${folderId}`);
        documents.value = response.data.map((doc, index) => ({
            ...doc, stt: index + 1, attachments: fakeAttachments
        }));
    } catch (error) { console.error('Lỗi lấy tài liệu:', error); }
};

watch(() => route.query.folder_id, async (folderId) => {
    if (!folderId) {
        documents.value = [];
        docForm.value.folder_id = null;
        return;
    }
    docForm.value.folder_id = parseInt(folderId);
    // Đóng toàn bộ các màn hình phụ khi chuyển đổi thư mục
    isCreating.value = false;
    isViewing.value = false; 
    await loadDocuments(folderId);
}, { immediate: true });

const handleEditorSaved = async () => {
    isCreating.value = false;
    if (docForm.value.folder_id) {
        await loadDocuments(docForm.value.folder_id);
    }
};

// Luồng phê duyệt Maker-Checker
const submitDocument = async (versionId, folderId) => {
    try {
        await api.post(`/documents/versions/${versionId}/submit`);
        alert('Đã trình tài liệu lên cấp quản lý thành công!');
        await loadDocuments(folderId);
    } catch (error) { alert(error.response?.data?.detail || 'Lỗi khi trình duyệt'); }
};

const approveDocument = async (versionId, folderId) => {
    try {
        await api.post(`/documents/versions/${versionId}/approve`);
        alert('Tài liệu đã được phê duyệt và ban hành chính thức!');
        await loadDocuments(folderId);
    } catch (error) { alert(error.response?.data?.detail || 'Lỗi khi phê duyệt'); }
};

const handleQuickView = (rowData) => { alert(`Mở cửa sổ xem nhanh: ${rowData.code}`); };

const getActionItems = (rowData) => {
    const latestVersion = rowData.versions && rowData.versions.length > 0 
                          ? rowData.versions[rowData.versions.length - 1] 
                          : null;
    if (!latestVersion) return [];

    const status = latestVersion.status;
    const versionId = latestVersion.id;
    const folderId = rowData.folder_id;

    let items = [
        { 
            label: 'Chi tiết & Vòng đời', 
            icon: 'pi pi-window-maximize', 
            // Đã gắn lệnh mở màn hình Chi tiết
            command: () => {
                selectedDocId.value = rowData.id;
                isViewing.value = true;
            } 
        },
        { separator: true }
    ];

    if (status === 'Draft') {
        items.push({ label: 'Trình phê duyệt', icon: 'pi pi-send', command: () => submitDocument(versionId, folderId) });
        items.push({ label: 'Tiếp tục soạn thảo', icon: 'pi pi-pencil', command: () => { isCreating.value = true; } });
    } 
    else if (status === 'Pending') {
        items.push({ label: 'Phê duyệt (Cấp quản lý)', icon: 'pi pi-check-circle', command: () => approveDocument(versionId, folderId) });
        items.push({ label: 'Từ chối & Yêu cầu sửa', icon: 'pi pi-times-circle', command: () => alert('Mở form từ chối') });
    } 
    else if (status === 'Active') {
        items.push({ label: 'Tạo phiên bản mới (Up version)', icon: 'pi pi-clone', command: () => alert('Nhân bản thành Version mới dạng Draft') });
        items.push({ label: 'Rà soát định kỳ', icon: 'pi pi-sync', command: () => alert('Nạp bằng chứng rà soát') });
        items.push({ label: 'Hủy/Lỗi thời (Admin)', icon: 'pi pi-trash', command: () => alert('Đánh dấu tài liệu lỗi thời') });
    }
    return items;
};
</script>

<template>
    <div v-if="!isCreating && !isViewing" class="card p-0 shadow-2 border-round overflow-hidden animate-fadein">
        
        <Toolbar class="border-none border-bottom-1 surface-border border-noround bg-surface-0 px-4 py-3">
            <template #start>
                <div class="flex align-items-center">
                    <span class="p-input-icon-left w-20rem">
                        <i class="pi pi-search" />
                        <InputText v-model="searchQuery" placeholder="Tìm kiếm tài liệu..." class="w-full" />
                    </span>
                </div>
            </template>
            <template #end>
                <Button label="Upload Tài liệu" icon="pi pi-upload" class="p-button-secondary mr-2" />
                <Button label="Soạn mới trực tuyến" icon="pi pi-pencil" class="p-button-success" :disabled="!docForm.folder_id" @click="isCreating = true" />
            </template>
        </Toolbar>

        <div class="p-4 overflow-y-auto bg-surface-50" style="min-height: calc(100vh - 16rem);">
            <DataTable :value="filteredDocuments" v-model:expandedRows="expandedRows" dataKey="id"
                       :paginator="true" :rows="10" responsiveLayout="scroll" 
                       class="p-datatable-sm shadow-1 border-round bg-white"
                       emptyMessage="Bấm chọn một thư mục trên Sidebar bên trái để hiển thị tài liệu.">
                
                <Column expander style="width: 3rem" />
                <Column field="stt" header="STT" style="width: 4rem"></Column>
                <Column field="code" header="Mã số ISO" :sortable="true"></Column>
                <Column field="title" header="Tên Tài liệu / Quy trình"></Column>
                <Column header="Phiên bản">
                    <template #body="slotProps">
                        <span v-if="slotProps.data.versions && slotProps.data.versions.length">
                            {{ slotProps.data.versions[slotProps.data.versions.length - 1].version_number }}
                        </span>
                    </template>
                </Column>
                <Column header="Trạng thái">
                    <template #body="slotProps">
                        <span v-if="slotProps.data.versions && slotProps.data.versions.length" 
                              :class="'badge status-' + slotProps.data.versions[slotProps.data.versions.length - 1].status.toLowerCase()">
                            {{ slotProps.data.versions[slotProps.data.versions.length - 1].status }}
                        </span>
                    </template>
                </Column>
                <Column header="Thao tác" style="width: 14rem">
                    <template #body="slotProps">
                        <SplitButton label="Xem nhanh" icon="pi pi-eye" 
                                     @click="handleQuickView(slotProps.data)" 
                                     :model="getActionItems(slotProps.data)" 
                                     class="p-button-sm p-button-outlined p-button-info" />
                    </template>
                </Column>

                <template #expansion="slotProps">
                    <div class="p-3 bg-gray-50 border-round m-3 border-1 surface-border">
                        <h6 class="text-primary mb-3"><i class="pi pi-paperclip mr-2"></i>Đính kèm: {{ slotProps.data.code }}</h6>
                        <DataTable :value="slotProps.data.attachments" class="p-datatable-sm bg-white">
                            <Column field="name" header="Tên File"></Column>
                            <Column field="type" header="Định dạng" style="width: 8rem">
                                <template #body="formProps">
                                    <Tag :severity="formProps.data.type === 'PDF' ? 'danger' : 'info'" :value="formProps.data.type" />
                                </template>
                            </Column>
                            <Column header="Thao tác" style="width: 10rem">
                                <template #body>
                                    <Button label="Tải xuống" icon="pi pi-download" class="p-button-sm p-button-text" />
                                </template>
                            </Column>
                        </DataTable>
                    </div>
                </template>
            </DataTable>
        </div>
    </div>

    <div v-else-if="isCreating">
        <DocumentEditor :folderId="docForm.folder_id" @close="isCreating = false" @saved="handleEditorSaved" />
    </div>

    <div v-else-if="isViewing">
        <DocumentDetail :documentId="selectedDocId" @close="isViewing = false" />
    </div>
</template>

<style scoped>
.badge {
    border-radius: 4px;
    padding: 0.3em 0.6rem;
    font-weight: bold;
    font-size: 11px;
}
.status-active { background-color: #d4edda; color: #155724; }
.status-draft { background-color: #fff3cd; color: #856404; }
.status-pending { background-color: #cce5ff; color: #004085; }
.status-obsolete { background-color: #f8d7da; color: #721c24; }
</style>