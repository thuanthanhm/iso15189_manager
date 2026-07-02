<script setup>
import { ref, defineProps, defineEmits } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/service/api';

const props = defineProps({ folderId: { type: Number, required: true } });
const emit = defineEmits(['close', 'saved']);
const toast = useToast();

const activeTab = ref('info');
const isSubmitting = ref(false);

const mainUploadRef = ref(null); // Liên kết với Component Upload file chính
const attachmentUploadRef = ref(null); // Liên kết với Component Upload biểu mẫu

const docForm = ref({
    code: '', title: '', doc_type: 'HTML_INTERNAL', content_html: '',
    folder_id: props.folderId, file_path: null
});
const attachments = ref([]);
const uploadedMainFileName = ref('');

const docTypeOptions = ref([
    { label: 'Bài viết HTML (Soạn trực tuyến)', value: 'HTML_INTERNAL' },
    { label: 'Tài liệu PDF (Upload file gốc)', value: 'PDF_INTERNAL' },
    { label: 'Tài liệu bên ngoài kiểm soát', value: 'EXTERNAL' }
]);

// 1. Upload File PDF gốc
const onMainFileUpload = async (event) => {
    const file = event.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await api.post('/documents/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        docForm.value.file_path = response.data.file_path; 
        uploadedMainFileName.value = response.data.original_name;
        
        toast.add({ severity: 'success', summary: 'Thành công', detail: 'Tài liệu gốc đã được tải lên máy chủ.', life: 3000 });
        mainUploadRef.value.clear(); // [ĐÃ SỬA]: Dọn dẹp thanh Progress Bar đúng chuẩn
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Lỗi Upload', detail: 'Không thể tải file PDF lên máy chủ.', life: 4000 });
    }
};

// 2. Upload Nhiều Biểu mẫu cùng lúc
const onAttachmentUpload = async (event) => {
    // Xử lý upload song song nhiều file
    const uploadPromises = event.files.map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/documents/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        attachments.value.push({
            file_name: response.data.original_name,
            file_path: response.data.file_path,
            file_type: response.data.file_type
        });
    });

    try {
        await Promise.all(uploadPromises);
        toast.add({ severity: 'success', summary: 'Hoàn tất', detail: `Đã tải lên ${event.files.length} biểu mẫu phụ.`, life: 3000 });
        attachmentUploadRef.value.clear(); // Dọn dẹp thanh Progress Bar sau khi tải xong
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Lỗi Upload', detail: 'Quá trình tải biểu mẫu phụ bị gián đoạn.', life: 4000 });
    }
};

const removeAttachment = (index) => { attachments.value.splice(index, 1); };

const saveFullDocument = async () => {
    if (!docForm.value.code || !docForm.value.title) {
        toast.add({ severity: 'warn', summary: 'Thiếu thông tin', detail: 'Bạn phải nhập Mã số và Tên tài liệu.', life: 3000 });
        return;
    }

    isSubmitting.value = true;
    try {
        docForm.value.attachments = attachments.value;
        await api.post('/documents/', docForm.value);
        toast.add({ severity: 'success', summary: 'Lưu thành công', detail: 'Bản nháp tài liệu đã được khởi tạo.', life: 3000 });
        emit('saved'); 
    } catch (error) {
        toast.add({ severity: 'error', summary: 'Hệ thống từ chối', detail: error.response?.data?.detail || 'Lỗi hệ thống khi lưu tài liệu', life: 5000 });
    } finally {
        isSubmitting.value = false;
    }
};
</script>

<template>
    <div class="workspace-editor animate-fadein relative">
        <Toast /> 
        
        <div class="p-3 border-bottom-1 surface-border bg-surface-0 flex justify-content-between align-items-center mb-3 sticky top-0 z-5">
            <div class="flex align-items-center gap-3">
                <Button icon="pi pi-arrow-left" class="p-button-text p-button-secondary" @click="emit('close')" title="Hủy bỏ" />
                <div>
                    <h5 class="m-0 font-bold text-xl text-primary">Tạo Bản Nháp (Draft) Tài Liệu Mới</h5>
                </div>
            </div>
            <div class="flex gap-2">
                <Button label="Hủy bỏ" icon="pi pi-times" class="p-button-text p-button-secondary" @click="emit('close')" :disabled="isSubmitting" />
                <Button label="Lưu & Khởi tạo" icon="pi pi-save" class="p-button-success shadow-1" @click="saveFullDocument" :loading="isSubmitting" />
            </div>
        </div>

        <div class="px-4 pb-4">
            <Tabs v-model:value="activeTab">
                <TabList class="mb-3">
                    <Tab value="info"><i class="pi pi-info-circle mr-2"></i>1. Định danh (Vỏ)</Tab>
                    <Tab value="content" :disabled="!docForm.code || !docForm.title"><i class="pi pi-file-edit mr-2"></i>2. Nội dung (Ruột)</Tab>
                    <Tab value="attachments" :disabled="!docForm.code || !docForm.title"><i class="pi pi-paperclip mr-2"></i>3. Biểu mẫu kèm theo</Tab>
                </TabList>

                <TabPanels class="bg-white border-1 surface-border border-round p-4 min-h-30rem">
                    
                    <TabPanel value="info" class="p-fluid grid">
                        <div class="col-12 md:col-6 field mb-3">
                            <label class="font-semibold mb-2 block">Mã số kiểm soát ISO <span class="text-red-500">*</span></label>
                            <InputText v-model="docForm.code" placeholder="VD: SOP.GPB.03" />
                        </div>
                        <div class="col-12 md:col-6 field mb-3">
                            <label class="font-semibold mb-2 block">Hình thức lưu trữ ruột tài liệu</label>
                            <Dropdown v-model="docForm.doc_type" :options="docTypeOptions" optionLabel="label" optionValue="value" />
                        </div>
                        <div class="col-12 field mb-3">
                            <label class="font-semibold mb-2 block">Tên quy trình / Tiêu đề <span class="text-red-500">*</span></label>
                            <InputText v-model="docForm.title" />
                        </div>
                        <div class="col-12 mt-3 text-center" v-if="docForm.code && docForm.title">
                            <Button label="Tiến tới bước Thiết lập Nội dung" icon="pi pi-arrow-right" class="w-auto p-button-outlined" @click="activeTab = 'content'" />
                        </div>
                    </TabPanel>

                    <TabPanel value="content">
                        <div v-if="docForm.doc_type === 'HTML_INTERNAL'" class="p-fluid">
                            <label class="font-semibold mb-2 block">Soạn thảo văn bản trực tuyến</label>
                            <Editor v-model="docForm.content_html" editorStyle="height: 400px" />
                        </div>

                        <div v-else-if="docForm.doc_type === 'PDF_INTERNAL'">
                            <div class="mb-3">
                                <span class="font-semibold block mb-1 text-lg">Tải lên tài liệu gốc (.PDF)</span>
                            </div>
                            <FileUpload ref="mainUploadRef" name="file" :multiple="false" accept=".pdf" :maxFileSize="50000000"
                                        customUpload @uploader="onMainFileUpload"
                                        emptyTemplate="Kéo và thả tệp PDF vào vùng này để upload.">
                                <template #empty>
                                    <div v-if="docForm.file_path" class="flex align-items-center justify-content-center flex-column text-success bg-green-50 border-round py-5 border-1 border-green-200 border-dashed">
                                        <i class="pi pi-check-circle text-5xl mb-2"></i>
                                        <span class="font-bold text-lg">Đã nhận diện file gốc: {{ uploadedMainFileName }}</span>
                                    </div>
                                    <div v-else class="flex align-items-center justify-content-center flex-column py-5">
                                        <i class="pi pi-cloud-upload text-5xl text-400 border-circle p-3 bg-surface-100 mb-3"></i>
                                        <p class="m-0 text-secondary">Kéo thả tài liệu PDF vào đây hoặc bấm nút Chọn (Choose).</p>
                                    </div>
                                </template>
                            </FileUpload>
                        </div>
                    </TabPanel>

                    <TabPanel value="attachments">
                        <div class="mb-3">
                            <span class="font-semibold block mb-1 text-lg">Hồ sơ / Biểu mẫu đính kèm</span>
                        </div>
                        <FileUpload ref="attachmentUploadRef" name="files" :multiple="true" accept=".pdf,.doc,.docx,.xls,.xlsx" :maxFileSize="20000000"
                                    customUpload @uploader="onAttachmentUpload"
                                    emptyTemplate="Kéo thả nhiều file Word/Excel vào đây.">
                            <template #empty>
                                <div class="flex align-items-center justify-content-center flex-column py-5">
                                    <i class="pi pi-copy text-5xl text-400 border-circle p-3 bg-surface-100 mb-3"></i>
                                    <p class="m-0 text-secondary">Kéo thả các biểu mẫu hồ sơ phụ (Word, Excel) vào vùng lưới này.</p>
                                </div>
                            </template>
                        </FileUpload>

                        <div class="mt-4" v-if="attachments.length > 0">
                            <h6 class="font-bold text-primary mb-2"><i class="pi pi-list mr-2"></i>Hồ sơ đang chờ phê duyệt đính kèm ({{ attachments.length }})</h6>
                            <DataTable :value="attachments" class="p-datatable-sm bg-surface-50 border-1 surface-border border-round">
                                <Column field="file_name" header="Tên Tệp Tin Gốc"></Column>
                                <Column field="file_type" header="Định dạng" style="width: 8rem">
                                    <template #body="slotProps"><Tag :severity="slotProps.data.file_type === 'PDF' ? 'danger' : 'info'" :value="slotProps.data.file_type" /></template>
                                </Column>
                                <Column header="Gỡ bỏ" style="width: 6rem">
                                    <template #body="slotProps">
                                        <Button icon="pi pi-trash" class="p-button-rounded p-button-danger p-button-text" @click="removeAttachment(slotProps.index)" />
                                    </template>
                                </Column>
                            </DataTable>
                        </div>
                    </TabPanel>
                    
                </TabPanels>
            </Tabs>
        </div>
    </div>
</template>

<style scoped>
.workspace-editor { background-color: var(--surface-card); border-radius: 12px; }
:deep(.p-tab) { padding: 1rem 1.5rem !important; font-weight: 600; }
</style>