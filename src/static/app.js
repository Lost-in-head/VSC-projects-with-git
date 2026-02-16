/**
 * eBay Listing Generator - Frontend JavaScript
 * Handles batch file uploads, drag-drop, and batch results display
 */

// DOM Elements
const uploadBox = document.getElementById('uploadBox');
const photoInput = document.getElementById('photoInput');
const previewSection = document.getElementById('previewSection');
const previewGrid = document.getElementById('previewGrid');
const photoCount = document.getElementById('photoCount');
const loadingSection = document.getElementById('loadingSection');
const loadingProgress = document.getElementById('loadingProgress');
const progressFill = document.getElementById('progressFill');
const resultsSection = document.getElementById('resultsSection');
const resultsGrid = document.getElementById('resultsGrid');
const resultCount = document.getElementById('resultCount');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');

const clearBtn = document.getElementById('clearBtn');
const submitBtn = document.getElementById('submitBtn');
const downloadAllBtn = document.getElementById('downloadAllBtn');
const newListingBtn = document.getElementById('newListingBtn');
const retryBtn = document.getElementById('retryBtn');

let selectedFiles = [];
let processedResults = [];

// Tab Management
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabBtns.forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

function switchTab(tabName) {
      // Update buttons
      tabBtns.forEach(btn => btn.classList.remove('active'));
      event.target.classList.add('active');

      // Update content
      tabContents.forEach(content => {
            content.style.display = 'none';
            content.classList.remove('active');
      });

      const activeTab = document.getElementById(`${tabName}Tab`);
      activeTab.style.display = 'block';
      activeTab.classList.add('active');

      // Load dashboard when switching to it
      if (tabName === 'dashboard') {
            loadDashboard();
      }
}

// Dashboard Functions
const refreshBtn = document.getElementById('refreshBtn');
if (refreshBtn) {
      refreshBtn.addEventListener('click', loadDashboard);
}

async function loadDashboard() {
      try {
            const response = await fetch('/api/listings');
            const listings = await response.json();

            if (!response.ok) {
                  console.error('Failed to load listings');
                  return;
            }

            displayDashboard(listings);
      } catch (error) {
            console.error('Error loading dashboard:', error);
      }
}

function displayDashboard(listings) {
      const tbody = document.getElementById('listingsBody');

      if (!listings || listings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px;">No listings yet. Generate some first! 📸</td></tr>';
            updateStats(0, 0, 0);
            return;
      }

      // Calculate stats
      let drafts = 0, published = 0;
      listings.forEach(l => {
            if (l.status === 'draft') drafts++;
            if (l.status === 'published') published++;
      });

      updateStats(listings.length, drafts, published);

      // Build table rows
      tbody.innerHTML = listings.map(listing => {
            const date = new Date(listing.created_at).toLocaleDateString();
            const statusClass = `status-${listing.status}`;
            return `
                  <tr>
                        <td><strong>${listing.title}</strong></td>
                        <td>${listing.brand || '-'} ${listing.model ? '(' + listing.model + ')' : ''}</td>
                        <td>$${listing.suggested_price ? listing.suggested_price.toFixed(2) : '-'}</td>
                        <td>
                              <span class="status-badge ${statusClass}">${listing.status}</span>
                        </td>
                        <td>${date}</td>
                        <td>
                              <div class="action-icons">
                                    <button class="action-btn" onclick="viewListing(${listing.id})" title="View Details">👁️</button>
                                    <button class="action-btn" onclick="togglePublished(${listing.id}, '${listing.status}')" title="Toggle Status">${listing.status === 'draft' ? '📤' : '📋'}</button>
                                    <button class="action-btn danger" onclick="deleteListing(${listing.id})" title="Delete">🗑️</button>
                              </div>
                        </td>
                  </tr>
            `;
      }).join('');
}

function updateStats(total, drafts, published) {
      document.getElementById('totalCount').textContent = total;
      document.getElementById('draftCount').textContent = drafts;
      document.getElementById('publishedCount').textContent = published;
}

function viewListing(listingId) {
      alert(`View listing ${listingId} - Full details view coming soon!`);
}

async function togglePublished(listingId, currentStatus) {
      const newStatus = currentStatus === 'draft' ? 'published' : 'draft';
      try {
            const response = await fetch(`/api/listings/${listingId}/status`, {
                  method: 'PATCH',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ status: newStatus })
            });

            if (response.ok) {
                  loadDashboard();
            }
      } catch (error) {
            console.error('Error updating status:', error);
      }
}

async function deleteListing(listingId) {
      if (!confirm('Are you sure you want to delete this listing?')) return;

      try {
            const response = await fetch(`/api/listings/${listingId}`, {
                  method: 'DELETE'
            });

            if (response.ok) {
                  loadDashboard();
            }
      } catch (error) {
            console.error('Error deleting listing:', error);
      }
}

// Event Listeners
uploadBox.addEventListener('click', () => photoInput.click());
uploadBox.addEventListener('dragover', handleDragOver);
uploadBox.addEventListener('dragleave', handleDragLeave);
uploadBox.addEventListener('drop', handleDrop);

photoInput.addEventListener('change', handleFileSelect);
clearBtn.addEventListener('click', clearPreview);
submitBtn.addEventListener('click', submitForm);
downloadAllBtn.addEventListener('click', downloadAllListings);
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
            handleFileInputs(files);
      }
}

function handleFileSelect(e) {
      const files = e.target.files;
      if (files.length > 0) {
            handleFileInputs(files);
      }
}

function handleFileInputs(fileList) {
      selectedFiles = [];
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
      const maxSize = 16 * 1024 * 1024;

      for (let file of fileList) {
            // Validate file type
            if (!allowedTypes.includes(file.type)) {
                  showError(`Invalid file type: ${file.name}. Use JPG, PNG, or GIF.`);
                  return;
            }

            // Validate file size
            if (file.size > maxSize) {
                  showError(`File too large: ${file.name}. Maximum 16MB allowed.`);
                  return;
            }

            selectedFiles.push(file);
      }

      if (selectedFiles.length > 0) {
            showPreview();
      }
}

function showPreview() {
      previewGrid.innerHTML = '';
      photoCount.textContent = selectedFiles.length;

      selectedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                  const previewItem = document.createElement('div');
                  previewItem.className = 'preview-item';
                  previewItem.innerHTML = `
                        <img src="${e.target.result}" alt="Preview ${index + 1}">
                        <button class="remove-btn" data-index="${index}">×</button>
                  `;

                  const removeBtn = previewItem.querySelector('.remove-btn');
                  removeBtn.addEventListener('click', () => removeFile(index));

                  previewGrid.appendChild(previewItem);
            };
            reader.readAsDataURL(file);
      });

      previewSection.style.display = 'block';
      uploadBox.style.display = 'none';
      errorSection.style.display = 'none';
}

function removeFile(index) {
      selectedFiles.splice(index, 1);
      if (selectedFiles.length === 0) {
            clearPreview();
      } else {
            showPreview();
      }
}

function clearPreview() {
      selectedFiles = [];
      photoInput.value = '';
      previewSection.style.display = 'none';
      uploadBox.style.display = 'block';
      errorSection.style.display = 'none';
}

async function submitForm() {
      if (selectedFiles.length === 0) {
            showError('Please select at least one photo first.');
            return;
      }

      try {
            // Show loading state
            previewSection.style.display = 'none';
            loadingSection.style.display = 'block';
            resultsSection.style.display = 'none';
            errorSection.style.display = 'none';

            processedResults = [];
            const totalFiles = selectedFiles.length;

            // Process each file
            for (let i = 0; i < selectedFiles.length; i++) {
                  const file = selectedFiles[i];
                  updateProgress(i, totalFiles, `Processing ${i + 1} of ${totalFiles}...`);

                  const formData = new FormData();
                  formData.append('photo', file);

                  try {
                        const response = await fetch('/api/upload', {
                              method: 'POST',
                              body: formData
                        });

                        const data = await response.json();

                        if (!response.ok || !data.success) {
                              console.warn(`Failed to process ${file.name}:`, data.error);
                              processedResults.push({
                                    filename: file.name,
                                    success: false,
                                    error: data.error || 'Unknown error'
                              });
                        } else {
                              processedResults.push({
                                    filename: file.name,
                                    success: true,
                                    data: data
                              });
                        }
                  } catch (error) {
                        console.warn(`Error processing ${file.name}:`, error);
                        processedResults.push({
                              filename: file.name,
                              success: false,
                              error: error.message
                        });
                  }
            }

            // Display results
            displayBatchResults();
            loadingSection.style.display = 'none';
            resultsSection.style.display = 'block';

      } catch (error) {
            console.error('Error:', error);
            showError('Batch processing failed: ' + error.message);
      }
}

function updateProgress(current, total, message) {
      const percentage = ((current + 1) / total) * 100;
      progressFill.style.width = percentage + '%';
      loadingProgress.textContent = message;
}

function displayBatchResults() {
      const successCount = processedResults.filter(r => r.success).length;
      resultCount.textContent = successCount;

      resultsGrid.innerHTML = '';

      processedResults.forEach((result, index) => {
            if (result.success) {
                  const card = createResultCard(result.data, result.filename, index);
                  resultsGrid.appendChild(card);
            } else {
                  const errorCard = createErrorCard(result.filename, result.error);
                  resultsGrid.appendChild(errorCard);
            }
      });
}

function createResultCard(data, filename, index) {
      const analysis = data.analysis;
      const listings = data.comparable_listings;
      const price = data.suggested_price;

      const card = document.createElement('div');
      card.className = 'result-card';

      // Build features list
      let featuresList = '';
      if (analysis.features) {
            const features = Array.isArray(analysis.features) ? analysis.features : [analysis.features];
            featuresList = features.map(f => `<li>${f}</li>`).join('');
      }

      // Build listings table
      let listingsTable = '';
      if (listings && listings.length > 0) {
            const rows = listings.map(item => `
                  <tr>
                        <td style="font-size: 0.9em;">${item.title || 'Unknown'}</td>
                        <td>$${parseFloat(item.price).toFixed(0)}</td>
                  </tr>
            `).join('');
            listingsTable = `
                  <div style="margin-top: 12px;">
                        <p style="font-size: 0.85em; color: #999; margin-bottom: 8px;">Similar listings:</p>
                        <table style="width: 100%; font-size: 0.85em;">
                              <tbody>${rows}</tbody>
                        </table>
                  </div>
            `;
      }

      card.innerHTML = `
            <h3 style="margin: 0 0 15px 0; color: #333; word-break: break-word;">
                  📷 ${filename}
            </h3>
            <div style="background: #f0f0f0; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
                  <p style="margin: 4px 0; font-size: 0.9em;"><strong>${analysis.brand || 'Unknown'} ${analysis.model || ''}</strong></p>
                  <p style="margin: 4px 0; font-size: 0.85em; color: #666;">${analysis.category || 'Unknown'}</p>
                  <p style="margin: 4px 0; font-size: 0.85em; color: #666;">Condition: ${analysis.condition || 'Unknown'}</p>
            </div>
            ${featuresList ? `<ul style="margin: 10px 0; padding-left: 20px; font-size: 0.85em;">${featuresList}</ul>` : ''}
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px; border-radius: 8px; text-align: center; margin: 15px 0;">
                  <p style="margin: 0; font-size: 0.85em; opacity: 0.9;">Suggested Price</p>
                  <p style="margin: 4px 0; font-size: 1.4em; font-weight: bold;">$${parseFloat(price).toFixed(2)}</p>
            </div>
            ${listingsTable}
            <button class="btn-secondary" style="width: 100%; margin-top: 12px;" onclick="copyPayload(${index})">📋 Copy Payload</button>
      `;

      // Store payload for copying
      card.dataset.payload = JSON.stringify(data.payload);

      return card;
}

function createErrorCard(filename, error) {
      const card = document.createElement('div');
      card.className = 'result-card';
      card.style.background = '#ffebee';
      card.style.borderLeft = '4px solid #f44336';

      card.innerHTML = `
            <h3 style="margin: 0 0 10px 0; color: #f44336;">❌ ${filename}</h3>
            <p style="margin: 0; color: #c62828; font-size: 0.9em;">${error}</p>
      `;

      return card;
}

function copyPayload(index) {
      const card = resultsGrid.children[index];
      const payload = card.dataset.payload;

      navigator.clipboard.writeText(payload).then(() => {
            const btn = card.querySelector('button');
            const originalText = btn.textContent;
            btn.textContent = '✓ Copied!';
            setTimeout(() => {
                  btn.textContent = originalText;
            }, 2000);
      }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Failed to copy to clipboard');
      });
}

function downloadAllListings() {
      const payloads = processedResults
            .filter(r => r.success)
            .map(r => r.data.payload);

      if (payloads.length === 0) {
            alert('No successful listings to download');
            return;
      }

      const json = JSON.stringify(payloads, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ebay-listings-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
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
      processedResults = [];
      progressFill.style.width = '0%';
}

// Auto-focus on page load
window.addEventListener('load', () => {
      uploadBox.focus();
});
