/**
 * eBay Listing Generator - Frontend JavaScript
 * Handles file upload, drag-drop, API calls, and results display
 */

// DOM Elements
const uploadBox = document.getElementById('uploadBox');
const photoInput = document.getElementById('photoInput');
const previewSection = document.getElementById('previewSection');
const previewImage = document.getElementById('previewImage');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');

const clearBtn = document.getElementById('clearBtn');
const submitBtn = document.getElementById('submitBtn');
const copyBtn = document.getElementById('copyBtn');
const newListingBtn = document.getElementById('newListingBtn');
const retryBtn = document.getElementById('retryBtn');

let selectedFile = null;

// Event Listeners
uploadBox.addEventListener('click', () => photoInput.click());
uploadBox.addEventListener('dragover', handleDragOver);
uploadBox.addEventListener('dragleave', handleDragLeave);
uploadBox.addEventListener('drop', handleDrop);

photoInput.addEventListener('change', handleFileSelect);
clearBtn.addEventListener('click', clearPreview);
submitBtn.addEventListener('click', submitForm);
copyBtn.addEventListener('click', copyToClipboard);
newListingBtn.addEventListener('click', resetForm);
retryBtn.addEventListener('click', resetForm);

// File Upload Handlers
function handleDragOver(e) {
      e.preventDefault();
      e.stopPropagation();
      uploadBox.classList.add('drag-over');
}

function handleDragLeave(e) {
      e.preventDefault();
      e.stopPropagation();
      uploadBox.classList.remove('drag-over');
}

function handleDrop(e) {
      e.preventDefault();
      e.stopPropagation();
      uploadBox.classList.remove('drag-over');

      const files = e.dataTransfer.files;
      if (files.length > 0) {
            handleFileInput(files[0]);
      }
}

function handleFileSelect(e) {
      const files = e.target.files;
      if (files.length > 0) {
            handleFileInput(files[0]);
      }
}

function handleFileInput(file) {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
      if (!allowedTypes.includes(file.type)) {
            showError('Invalid file type. Please use JPG, PNG, or GIF.');
            return;
      }

      // Validate file size (16MB)
      const maxSize = 16 * 1024 * 1024;
      if (file.size > maxSize) {
            showError('File too large. Maximum 16MB allowed.');
            return;
      }

      selectedFile = file;
      showPreview(file);
}

function showPreview(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
            previewImage.src = e.target.result;
            previewSection.style.display = 'block';
            uploadBox.style.display = 'none';
            errorSection.style.display = 'none';
      };
      reader.readAsDataURL(file);
}

function clearPreview() {
      selectedFile = null;
      photoInput.value = '';
      previewSection.style.display = 'none';
      uploadBox.style.display = 'block';
      errorSection.style.display = 'none';
}

async function submitForm() {
      if (!selectedFile) {
            showError('Please select a photo first.');
            return;
      }

      const formData = new FormData();
      formData.append('photo', selectedFile);

      try {
            // Show loading state
            previewSection.style.display = 'none';
            loadingSection.style.display = 'block';
            resultsSection.style.display = 'none';
            errorSection.style.display = 'none';

            // Send to backend
            const response = await fetch('/api/upload', {
                  method: 'POST',
                  body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                  throw new Error(data.error || 'Upload failed');
            }

            if (!data.success) {
                  throw new Error(data.error || 'Processing failed');
            }

            // Display results
            displayResults(data);
            loadingSection.style.display = 'none';
            resultsSection.style.display = 'block';

      } catch (error) {
            console.error('Error:', error);
            showError(error.message);
      }
}

function displayResults(data) {
      // Display image analysis
      const analysis = data.analysis;
      const analysisDiv = document.getElementById('analysisResults');

      analysisDiv.innerHTML = `
        <div class="info-item">
            <div class="info-label">Brand</div>
            <div class="info-value">${analysis.brand || 'Unknown'}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Model</div>
            <div class="info-value">${analysis.model || 'Unknown'}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Category</div>
            <div class="info-value">${analysis.category || 'Unknown'}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Condition</div>
            <div class="info-value">${analysis.condition || 'Unknown'}</div>
        </div>
        ${analysis.features ? `
            <div class="info-item info-features">
                <div class="info-label">Features</div>
                <ul>
                    ${Array.isArray(analysis.features)
                        ? analysis.features.map(f => `<li>${f}</li>`).join('')
                        : `<li>${analysis.features}</li>`
                  }
                </ul>
            </div>
        ` : ''}
    `;

      // Display comparable listings
      const listings = data.comparable_listings;
      const listingsDiv = document.getElementById('listingsResults');

      if (listings && listings.length > 0) {
            const tableRows = listings.map(item => `
            <tr>
                <td>${item.title || 'Unknown'}</td>
                <td>$${parseFloat(item.price).toFixed(2)}</td>
                <td>${item.condition || 'Unknown'}</td>
            </tr>
        `).join('');

            listingsDiv.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Price</th>
                        <th>Condition</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        `;
      } else {
            listingsDiv.innerHTML = '<p>No comparable listings found.</p>';
      }

      // Display price
      const priceDiv = document.getElementById('priceResults');
      const price = data.suggested_price;
      priceDiv.innerHTML = `$${parseFloat(price).toFixed(2)}`;

      // Display payload
      const payloadDiv = document.getElementById('payloadResults');
      payloadDiv.innerHTML = JSON.stringify(data.payload, null, 2);
}

function copyToClipboard() {
      const payload = document.getElementById('payloadResults').textContent;
      navigator.clipboard.writeText(payload).then(() => {
            // Show feedback
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '✓ Copied!';
            setTimeout(() => {
                  copyBtn.textContent = originalText;
            }, 2000);
      }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Failed to copy to clipboard');
      });
}

function showError(message) {
      errorMessage.textContent = message;
      errorSection.style.display = 'block';
      loadingSection.style.display = 'none';
      previewSection.style.display = 'none';
      resultsSection.style.display = 'none';
}

function resetForm() {
      clearPreview();
      resultsSection.style.display = 'none';
      loadingSection.style.display = 'none';
}

// Auto-focus on page load
window.addEventListener('load', () => {
      uploadBox.focus();
});
