/**
 * Document Upload Dropzone & Preview Handler
 */
document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('upload_dropzone');
  const fileInput = document.getElementById('doc_file_input');
  const selectedFileInfo = document.getElementById('selected_file_info');
  const fileNameDisplay = document.getElementById('file_name_display');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--primary-600)';
      dropzone.style.backgroundColor = 'var(--primary-50)';
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.style.borderColor = '';
      dropzone.style.backgroundColor = '';
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = '';
      dropzone.style.backgroundColor = '';
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelection(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        handleFileSelection(fileInput.files[0]);
      }
    });

    function handleFileSelection(file) {
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds the 5MB limit. Please upload a smaller file.');
        fileInput.value = '';
        if (selectedFileInfo) selectedFileInfo.style.display = 'none';
        return;
      }

      // Display filename
      if (fileNameDisplay && selectedFileInfo) {
        fileNameDisplay.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        selectedFileInfo.style.display = 'block';
      }
    }
  }

  // Document Preview Modal
  window.previewDocument = function(url, filename, mime) {
    const previewContainer = document.getElementById('preview_content');
    const previewTitle = document.getElementById('preview_modal_title');
    if (!previewContainer) return;

    previewTitle.textContent = `Viewing: ${filename}`;
    previewContainer.innerHTML = '';

    if (mime.startsWith('image/')) {
      const img = document.createElement('img');
      img.src = url;
      img.style.maxWidth = '100%';
      img.style.maxHeight = '500px';
      img.style.display = 'block';
      img.style.margin = '0 auto';
      img.style.borderRadius = '8px';
      previewContainer.appendChild(img);
    } else if (mime === 'application/pdf') {
      const iframe = document.createElement('iframe');
      iframe.src = url;
      iframe.style.width = '100%';
      iframe.style.height = '500px';
      iframe.style.border = 'none';
      previewContainer.appendChild(iframe);
    } else {
      previewContainer.innerHTML = `
        <div style="text-align:center; padding: 40px 20px;">
          <p>Preview not directly supported in this browser frame.</p>
          <a href="${url}" target="_blank" class="btn btn-primary" style="margin-top: 14px;">Download Document</a>
        </div>
      `;
    }

    openModal('doc_preview_modal');
  };
});
