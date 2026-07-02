<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';
import api from '@/service/api';

const route = useRoute();
const props = defineProps({ documentId: { type: Number, required: true } });
const emit = defineEmits(['close']);

const activeTab = ref('forms'); 
const docData = ref(null);
const loading = ref(true);
const isSigned = ref(false);
const signing = ref(false);
const missingToken = ref(false);

const displayPreview = ref(false);
const previewData = ref(null);

const pdfCanvasContainer = ref(null);
const isPdfRendering = ref(false);

// Đồng bộ trạng thái ID tài liệu từ route hoặc props truyền vào
const currentDocId = ref(props.documentId);

const loadDocumentDetail = async () => {
    loading.value = true;
    try {
        const folderId = route.query.folder_id; 
        const response = await api.get(`/documents/folder/${folderId}`); 
        docData.value = response.data.find(d => d.id === currentDocId.value);
        
        if (latestVersion.value?.pdf_path && docData.value?.doc_type === 'PDF_INTERNAL') {
            nextTick(() => { initPdfJsAndRender(); });
        }
    } catch (error) {
        console.error('Lỗi tải thông tin chi tiết quy trình:', error);
    } finally {
        loading.value = false;
    }
};

const latestVersion = computed(() => {
    if (docData.value && docData.value.versions && docData.value.versions.length > 0) {
        return docData.value.versions[docData.value.versions.length - 1];
    }
    return null;
});

const getAuthenticatedStreamUrl = (versionId) => {
    if (!versionId) return null;
    const token = localStorage.getItem('access_token') || localStorage.getItem('token') || ''; 
    if (!token) {
        missingToken.value = true; return null;
    }
    missingToken.value = false;
    return `http://127.0.0.1:8000/documents/stream/${versionId}?token=${token}`;
};

// CƠ CHẾ KHỞI TẠO BẤT TỬ PDF.JS KHÔNG LO CRASH VITE
const initPdfJsAndRender = () => {
    isPdfRendering.value = true;
    if (window.pdfjsLib) {
        renderPdfToCanvas();
        return;
    }
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
    script.onload = () => {
        window.pdfjsLib = window['pdfjs-dist/build/pdf'];
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        renderPdfToCanvas();
    };
    document.head.appendChild(script);
};

// ENGINE XỬ LÝ CANVAS HOÀ TRỘN WATERMARK ĐỘNG TRÊN RAM CLIENT
const renderPdfToCanvas = async () => {
    const streamUrl = getAuthenticatedStreamUrl(latestVersion.value?.id);
    if (!streamUrl || !pdfCanvasContainer.value) {
        isPdfRendering.value = false;
        return;
    }
    pdfCanvasContainer.value.innerHTML = ''; 

    try {
        const loadingTask = window.pdfjsLib.getDocument(streamUrl);
        const pdf = await loadingTask.promise;
        
        const username = localStorage.getItem('username') || 'Nhân viên hệ thống';
        const timestamp = new Date().toLocaleString('vi-VN');

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
            const page = await pdf.getPage(pageNum);
            const viewport = page.getViewport({ scale: 1.8 }); 
            
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            
            canvas.style.width = '100%';
            canvas.style.maxWidth = '920px'; 
            canvas.style.boxShadow = '0 8px 16px rgba(0,0,0,0.12)';
            canvas.style.borderRadius = '4px';
            canvas.style.display = 'block';
            canvas.style.margin = '0 auto 25px auto';

            pdfCanvasContainer.value.appendChild(canvas);
            await page.render({ canvasContext: ctx, viewport: viewport }).promise;

            // DẬP MỘC BẢO MẬT ĐA DÒNG
            ctx.save();
            ctx.translate(canvas.width / 2, canvas.height / 2); 
            ctx.rotate(-Math.PI / 5); 
            ctx.fillStyle = 'rgba(255, 0, 0, 0.14)'; 
            ctx.textAlign = 'center';
            
            ctx.font = 'bold 46px Arial';
            ctx.fillText('TÀI LIỆU KIỂM SOÁT - GPB BVUB', 0, -50);
            ctx.font = 'bold 32px Arial';
            ctx.fillText('LƯU HÀNH NỘI BỘ', 0, 0);
            ctx.font = 'italic 22px Arial';
            ctx.fillText(`Truy cập bởi: ${username}`, 0, 45);
            ctx.fillText(`Thời gian: ${timestamp}`, 0, 80);
            ctx.restore();
        }
    } catch (error) {
        console.error('Lỗi luồng vẽ Canvas PDF:', error);
    } finally {
        isPdfRendering.value = false;
    }
};

const getFileUrl = (path) => {
    if (!path) return null;
    if (path.includes('\\')) return `http://127.0.0.1:8000/uploads/${path.split('\\').pop()}`;
    return `http://127.0.0.1:8000/${path}`;
};

const dynamicHistory = computed(() => {
    if (!latestVersion.value) return [];
    return [
        { action: `Khởi tạo bản nháp (v${latestVersion.value.version_number})`, user: 'Kỹ thuật viên', time: 'Hệ thống' },
        { action: 'Ban hành văn bản', user: 'Quản lý chất lượng', time: 'Đã phê duyệt chính thức' }
    ];
});

const documentAttachments = computed(() => latestVersion.value?.attachments || []);
const forceDownload = (path) => { window.open(getFileUrl(path), '_blank'); };
const previewAttachment = (att) => { previewData.value = att; displayPreview.value = true; };
const getAttachmentActions = (att) => [{ label: 'Tải về', icon: 'pi pi-download', command: () => forceDownload(att.file_path) }];

const handleSignReadAndUnderstood = () => {
    signing.value = true; setTimeout(() => { isSigned.value = true; signing.value = false; }, 600);
};

// Theo dõi sự thay đổi ID từ Router của thanh điều hướng ngữ cảnh bên cạnh gửi qua
watch(() => route.params.id, (newId) => {
    if (newId) {
        currentDocId.value = Number(newId);
        loadDocumentDetail();
    }
});

onMounted(() => { loadDocumentDetail(); });
</script>

<template>
    <div class="qms-detail-container card p-0 overflow-hidden" v-if="docData">
        <div class="flex flex-row align-items-stretch w-full h-full">
            
            <div class="flex-1 position-relative bg-gray-300 flex flex-column text-center justify-content-center border-none">
                
                <div v-if="isPdfRendering" class="flex flex-column align-items-center justify-content-center h-full text-surface-600 py-6">
                    <i class="pi pi-spin pi-spinner text-5xl mb-3 text-primary"></i>
                    <span class="font-medium text-lg">Hệ thống đang giải mã và kết xuất tài liệu an toàn...</span>
                </div>

                <div v-if="missingToken" class="flex flex-column align-items-center justify-content-center h-full text-surface-700 p-4">
                    <i class="pi pi-lock text-5xl text-danger mb-3"></i>
                    <h4>Hết hạn phiên truy cập hệ thống an toàn</h4>
                </div>

                <div v-show="!isPdfRendering && docData.doc_type === 'PDF_INTERNAL'" 
                     ref="pdfCanvasContainer" 
                     class="pdf-scroll-viewport"
                     style="height: calc(100vh - 12rem); overflow-y: auto; overflow-x: hidden; padding: 2rem 1.5rem;">
                     </div>

                <div v-if="docData.doc_type === 'HTML_INTERNAL'" class="bg-white p-5 m-4 border-round shadow-2 overflow-y-auto text-left line-height-3 text-lg border-1 surface-border" style="height: calc(100vh - 12rem);">
                    <div v-html="latestVersion?.content_html"></div>
                </div>
            </div>

            <div class="qms-right-panel bg-white border-left-1 surface-border flex flex-column">
                
                <div class="p-4 border-bottom-1 surface-border bg-surface-50 flex flex-column gap-3">
                    <Button label="Quay lại danh sách" icon="pi pi-arrow-left" class="p-button-text p-button-secondary p-button-sm justify-content-start px-0" @click="emit('close')" />
                    
                    <div>
                        <div class="flex align-items-center gap-2 mb-2">
                            <span class="font-bold text-2xl text-primary-700">{{ docData.code }}</span>
                            <Tag :value="'Bản v' + (latestVersion?.version_number || '1.0')" severity="info" class="font-bold" />
                        </div>
                        <div class="text-surface-900 font-bold text-base line-height-3 text-ellipse-header">{{ docData.title }}</div>
                    </div>
                    
                    <Button v-if="!isSigned" label="Ký xác nhận Đã đọc & Hiểu" icon="pi pi-user-edit" class="p-button-warning w-full shadow-1 font-bold p-3 text-md" :loading="signing" @click="handleSignReadAndUnderstood" />
                    <Button v-else label="Đã hoàn tất ký văn bản" icon="pi pi-verified" class="p-button-success p-button-outlined w-full p-3 font-bold" disabled />
                </div>

                <div class="flex-1 overflow-y-auto p-3 bg-white">
                    <Tabs v-model:value="activeTab">
                        <TabList>
                            <Tab value="forms" class="flex-1 text-center font-bold text-sm"><i class="pi pi-paperclip mr-1.5"></i>Biểu mẫu ({{ documentAttachments.length }})</Tab>
                            <Tab value="lifecycle" class="flex-1 text-center font-bold text-sm"><i class="pi pi-history mr-1.5"></i>Vòng đời</Tab>
                        </TabList>
                        
                        <TabPanels class="px-0 py-3">
                            <TabPanel value="forms">
                                <DataTable :value="documentAttachments" class="p-datatable-sm border-1 surface-border border-round" emptyMessage="Không có hồ sơ mẫu đính kèm.">
                                    <Column field="file_name" header="Tên tài liệu phụ" class="text-xs"></Column>
                                    <Column style="width: 4rem">
                                        <template #body="slotProps">
                                            <SplitButton icon="pi pi-eye" @click="previewAttachment(slotProps.data)" :model="getAttachmentActions(slotProps.data)" class="p-button-sm p-button-text p-button-secondary" />
                                        </template>
                                    </Column>
                                </DataTable>
                            </TabPanel>

                            <TabPanel value="lifecycle">
                                <Timeline :value="dynamicHistory" class="custom-timeline p-2">
                                    <template #content="slotProps">
                                        <div class="text-xs font-bold text-surface-900 line-height-2">{{ slotProps.item.action }}</div>
                                        <div class="text-muted mt-1" style="font-size: 11px;"><i class="pi pi-user mr-1"></i>{{ slotProps.item.user }}</div>
                                    </template>
                                </Timeline>
                            </TabPanel>
                        </TabPanels>
                    </Tabs>
                </div>
            </div>

        </div>

        <Dialog v-model:visible="displayPreview" :header="previewData?.file_name" :style="{ width: '70vw' }" :modal="true">
            <div v-if="previewData?.file_type === 'PDF'" style="height: 70vh;">
                <iframe :src="getFileUrl(previewData.file_path) + '#toolbar=0'" width="100%" height="100%" style="border: none;"></iframe>
            </div>
            <div v-else class="text-center p-5">
                <Button label="Tải tệp mẫu về máy" icon="pi pi-download" @click="forceDownload(previewData.file_path)" />
            </div>
        </Dialog>
    </div>
</template>

<style scoped>
/* Đồng bộ đồng đều kích thước tổng thể với khung view của template Sakai */
.qms-detail-container {
    height: calc(100vh - 8rem);
    width: 100%;
}

/* Khóa cứng kích thước cột phải */
.qms-right-panel {
    width: 350px;
    flex-shrink: 0;
    height: 100%;
}

/* SỬA LỖI CSS VS CODE THEO YÊU CẦU ĐẶC TẢ */
.text-ellipse {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2; /* Nằm chính xác bên dưới -webkit-line-clamp */
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.4;
}

.text-ellipse-header {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Định dạng thanh cuộn vùng Canvas giống Adobe Acrobat */
.pdf-scroll-viewport::-webkit-scrollbar { 
    width: 10px; 
}
.pdf-scroll-viewport::-webkit-scrollbar-track { 
    background: #323639; 
}
.pdf-scroll-viewport::-webkit-scrollbar-thumb { 
    background: #5a5d60; 
    border-radius: 5px; 
    border: 2px solid #323639;
}
.pdf-scroll-viewport::-webkit-scrollbar-thumb:hover { 
    background: #7e8184; 
}

:deep(.p-tab) { padding: 0.75rem 0.25rem !important; font-weight: bold; }
:deep(.custom-timeline .p-timeline-event-content) { padding: 0 0 1.5rem 0.8rem !important; }
:deep(.custom-timeline .p-timeline-event-opposite) { display: none !important; }
</style>