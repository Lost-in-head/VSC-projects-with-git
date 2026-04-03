/**
 * eBay Listing Generator - Frontend JavaScript
 * Handles batch file uploads, drag-drop, and batch results display
 */

// Configurable API base URL.  Set window.__API_BASE_URL__ before this script
// loads to point at a remote server (e.g. for mobile/desktop builds).
// Defaults to '' so all relative /api/* calls work when served by Flask.
const API_BASE_URL = window.__API_BASE_URL__ || '';

// HTML escaping utility to prevent XSS when injecting API data into the DOM
function escapeHtml(str) {
      if (str === null || str === undefined) return '';
      return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
}

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
const connectEbayBtn = document.getElementById('connectEbayBtn');
const ebayConnectionStatus = document.getElementById('ebayConnectionStatus');

// State is managed by appState (state.js)

// ── File Validation ──────────────────────────────────────────────────────────

class FileValidator {
      static ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/gif']);
      static MAX_SIZE_BYTES = 16 * 1024 * 1024; // 16MB
      static MAX_FILES = 50;

      static validateFile(file) {
            const errors = [];
            if (!this.ALLOWED_TYPES.has(file.type)) {
                  errors.push(`${file.name}: Invalid type ${file.type}`);
            }
            if (file.size > this.MAX_SIZE_BYTES) {
                  const sizeMb = (file.size / 1024 / 1024).toFixed(1);
                  errors.push(`${file.name}: Too large (${sizeMb}MB > 16MB)`);
            }
            if (file.size === 0) {
                  errors.push(`${file.name}: File is empty`);
            }
            return errors;
      }

      static validateBatch(files) {
            const errors = [];
            if (files.length > this.MAX_FILES) {
                  errors.push(`Too many files (${files.length} > ${this.MAX_FILES})`);
                  return { valid: [], errors };
            }
            const validFiles = [];
            for (const file of files) {
                  const fileErrors = this.validateFile(file);
                  if (fileErrors.length) {
                        errors.push(...fileErrors);
                  } else {
                        validFiles.push(file);
                  }
            }
            return { valid: validFiles, errors };
      }
}

// ── Accessibility helpers ────────────────────────────────────────────────────

function announceToScreenReaders(message) {
      const announcement = document.createElement('div');
      announcement.className = 'sr-only';
      announcement.setAttribute('aria-live', 'assertive');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.textContent = message;
      document.body.appendChild(announcement);
      setTimeout(() => announcement.remove(), 1000);
}


function setSectionVisibility(section, visible, displayValue = 'block') {
      section.classList.toggle('hidden', !visible);
      section.style.display = visible ? displayValue : 'none';
}


function updateEbayConnectionUI() {
      if (!ebayConnectionStatus || !connectEbayBtn) return;
      ebayConnectionStatus.textContent = appState.isEbayConnected() ? 'Connected (Mock OAuth)' : 'Not Connected';
      ebayConnectionStatus.classList.toggle('connected', appState.isEbayConnected());
      ebayConnectionStatus.classList.toggle('disconnected', !appState.isEbayConnected());
      connectEbayBtn.textContent = appState.isEbayConnected() ? '✅ eBay Connected' : '🔐 Connect eBay';
}

function notifyHighValueCards(highValueCount) {
      if (highValueCount <= 0) return;
      const message = `🔥 ${highValueCount} high-value card(s) found (threshold: $20)!`;

      if ('Notification' in window) {
            if (Notification.permission === 'granted') {
                  new Notification(message);
                  return;
            }
            if (Notification.permission !== 'denied') {
                  Notification.requestPermission().then(permission => {
                        if (permission === 'granted') {
                              new Notification(message);
                        } else {
                              alert(message);
                        }
                  });
                  return;
            }
      }

      alert(message);
}

async function listForSale(listingId) {
      if (!listingId) {
            alert('Listing ID missing for publish action.');
            return;
      }
      if (!appState.isEbayConnected()) {
            alert('Please click Connect eBay first (mock OAuth).');
            return;
      }

      try {
            const response = await fetch(`${API_BASE_URL}/api/listings/${listingId}/publish`, { method: 'POST' });
            const data = await response.json();
            if (!response.ok) {
                  throw new Error(data.error || 'Publish failed');
            }
            alert(`✅ Listed for sale! External ID: ${data.external_listing_id}`);
      } catch (error) {
            alert(`❌ List for Sale failed: ${error.message}`);
      }
}

// Tab Management
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabBtns.forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.tab, btn));
});

function switchTab(tabName, clickedBtn = null) {
      // Update buttons
      tabBtns.forEach(btn => btn.classList.remove('active'));
      if (clickedBtn) {
            clickedBtn.classList.add('active');
      }

      // Update content
      tabContents.forEach(content => {
            content.style.display = 'none';
            content.classList.remove('active');
            content.classList.add('hidden');
      });

      const activeTab = document.getElementById(`${tabName}Tab`);
      activeTab.style.display = 'block';
      activeTab.classList.add('active');
      activeTab.classList.remove('hidden');

      appState.switchTab(tabName);
}

// Dashboard Functions
const refreshBtn = document.getElementById('refreshBtn');
if (refreshBtn) {
      refreshBtn.addEventListener('click', loadDashboard);
}

async function loadDashboard() {
      try {
            const response = await fetch(`${API_BASE_URL}/api/listings`);
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

      // Build table rows using data-* attributes and CSS classes (no inline onclick)
      tbody.innerHTML = listings.map(listing => {
            const date = new Date(listing.created_at).toLocaleDateString();
            const statusClass = `status-${escapeHtml(listing.status)}`;
            const toggleLabel = listing.status === 'draft' ? 'Publish listing' : 'Move to draft';
            return `
                  <tr data-listing-id="${listing.id}" data-status="${escapeHtml(listing.status)}">
                        <td><strong>${escapeHtml(listing.title)}</strong></td>
                        <td>${escapeHtml(listing.brand || '-')} ${listing.model ? '(' + escapeHtml(listing.model) + ')' : ''}</td>
                        <td>$${listing.suggested_price ? listing.suggested_price.toFixed(2) : '-'}</td>
                        <td>
                              <span class="status-badge ${statusClass}">${escapeHtml(listing.status)}</span>
                        </td>
                        <td>${escapeHtml(date)}</td>
                        <td>
                              <div class="action-icons">
                                    <button class="action-btn view-btn" title="View Details" aria-label="View details for ${escapeHtml(listing.title)}">👁️</button>
                                    <button class="action-btn toggle-btn" title="Toggle Status" aria-label="${toggleLabel} for ${escapeHtml(listing.title)}">${listing.status === 'draft' ? '📤' : '📋'}</button>
                                    <button class="action-btn danger delete-btn" title="Delete" aria-label="Delete ${escapeHtml(listing.title)}">🗑️</button>
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

// Event delegation for dashboard table actions
document.getElementById('listingsBody').addEventListener('click', (e) => {
      const viewBtn = e.target.closest('.view-btn');
      const deleteBtn = e.target.closest('.delete-btn');
      const toggleBtn = e.target.closest('.toggle-btn');

      if (viewBtn) {
            const row = viewBtn.closest('tr');
            viewListing(parseInt(row.dataset.listingId, 10));
      }
      if (deleteBtn) {
            const row = deleteBtn.closest('tr');
            deleteListing(parseInt(row.dataset.listingId, 10));
      }
      if (toggleBtn) {
            const row = toggleBtn.closest('tr');
            togglePublished(parseInt(row.dataset.listingId, 10), row.dataset.status);
      }
});

// Subscribe to tab changes to auto-load dashboard
appState.subscribe(({ key }) => {
      if (key === 'currentTab' && appState.getCurrentTab() === 'dashboard') {
            loadDashboard();
      }
});

function viewListing(listingId) {
      fetch(`${API_BASE_URL}/api/listings/${listingId}`)
            .then(r => r.json())
            .then(listing => {
                  const overlay = document.createElement('div');
                  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px;';

                  const modal = document.createElement('div');
                  modal.style.cssText = 'background:#fff;border-radius:12px;padding:28px;max-width:560px;width:100%;max-height:85vh;overflow-y:auto;position:relative;box-shadow:0 20px 60px rgba(0,0,0,.3);';

                  const comparables = Array.isArray(listing.comparable_listings) && listing.comparable_listings.length
                        ? listing.comparable_listings.map(c => {
                              const price = c.price != null ? parseFloat(c.price).toFixed(2) : '?';
                              return `<li>$${price} — ${escapeHtml(c.title || '')}</li>`;
                        }).join('')
                        : '<li>None</li>';

                  const features = Array.isArray(listing.features) && listing.features.length
                        ? listing.features.map(f => `<li>${escapeHtml(f)}</li>`).join('')
                        : '<li>—</li>';

                  const priceDisplay = listing.suggested_price !== null && listing.suggested_price !== undefined
                        ? `$${listing.suggested_price.toFixed(2)}`
                        : '—';

                  modal.innerHTML = `
                        <button class="modal-close-btn" style="position:absolute;top:12px;right:16px;background:none;border:none;font-size:1.5em;cursor:pointer;color:#666;" aria-label="Close listing details">×</button>
                        <h2 style="margin:0 0 16px;color:#333;font-size:1.2em;">${escapeHtml(listing.title)}</h2>
                        <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
                              <tr><td style="padding:6px 0;color:#999;width:140px;">Brand / Model</td><td>${escapeHtml(listing.brand || '—')} ${listing.model ? '/ ' + escapeHtml(listing.model) : ''}</td></tr>
                              <tr><td style="padding:6px 0;color:#999;">Category</td><td>${escapeHtml(listing.category || '—')}</td></tr>
                              <tr><td style="padding:6px 0;color:#999;">Condition</td><td>${escapeHtml(listing.condition || '—')}</td></tr>
                              <tr><td style="padding:6px 0;color:#999;">Suggested Price</td><td><strong>${priceDisplay}</strong></td></tr>
                              <tr><td style="padding:6px 0;color:#999;">Status</td><td>${escapeHtml(listing.status)}</td></tr>
                              ${listing.external_listing_id ? `<tr><td style="padding:6px 0;color:#999;">External ID</td><td>${escapeHtml(listing.external_listing_id)}</td></tr>` : ''}
                              ${listing.publish_error ? `<tr><td style="padding:6px 0;color:#999;">Publish Error</td><td style="color:#c62828;">${escapeHtml(listing.publish_error)}</td></tr>` : ''}
                        </table>
                        <p style="margin:14px 0 4px;color:#999;font-size:0.85em;">Features</p>
                        <ul style="margin:0;padding-left:18px;font-size:0.85em;">${features}</ul>
                        <p style="margin:14px 0 4px;color:#999;font-size:0.85em;">Comparable Listings</p>
                        <ul style="margin:0;padding-left:18px;font-size:0.85em;">${comparables}</ul>
                        <details style="margin-top:14px;">
                              <summary style="cursor:pointer;font-size:0.85em;color:#667eea;">eBay Payload JSON</summary>
                              <pre style="background:#2d2d2d;color:#f8f8f2;padding:12px;border-radius:8px;overflow-x:auto;font-size:0.78em;margin-top:8px;">${escapeHtml(JSON.stringify(listing.payload, null, 2))}</pre>
                        </details>
                  `;

                  overlay.className = 'listing-modal-overlay';
                  overlay.appendChild(modal);
                  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
                  modal.querySelector('.modal-close-btn').addEventListener('click', () => overlay.remove());
                  document.body.appendChild(overlay);
            })
            .catch(() => alert(`Could not load listing ${listingId}.`));
}

async function togglePublished(listingId, currentStatus) {
      const newStatus = currentStatus === 'draft' ? 'published' : 'draft';
      try {
            const response = await fetch(`${API_BASE_URL}/api/listings/${listingId}/status`, {
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
            const response = await fetch(`${API_BASE_URL}/api/listings/${listingId}`, {
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
uploadBox.addEventListener('dragover', handleDragOver);
uploadBox.addEventListener('dragleave', handleDragLeave);
uploadBox.addEventListener('drop', handleDrop);

// Keyboard activation for the upload box (Enter/Space)
uploadBox.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            photoInput.click();
      }
});

photoInput.addEventListener('change', handleFileSelect);
clearBtn.addEventListener('click', clearPreview);
submitBtn.addEventListener('click', submitForm);
downloadAllBtn.addEventListener('click', downloadAllListings);
newListingBtn.addEventListener('click', resetForm);
retryBtn.addEventListener('click', resetForm);
if (connectEbayBtn) {
      connectEbayBtn.addEventListener('click', () => {
            appState.setEbayConnected(true);
            updateEbayConnectionUI();
            alert('✅ eBay connected successfully (mock OAuth).');
      });
}

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
      const { valid, errors } = FileValidator.validateBatch(Array.from(fileList));

      if (errors.length) {
            showError(`Invalid files:\n${errors.join('\n')}`);
            return;
      }

      appState.clearError();
      appState.addFiles(valid);
      showPreview();
}

// Delegated click handler for the preview grid remove buttons (defined once)
previewGrid.addEventListener('click', (e) => {
      const btn = e.target.closest('.remove-btn');
      if (btn) {
            const idx = parseInt(btn.dataset.index, 10);
            removeFile(idx);
      }
});

// Delegated click handler for result card action buttons
resultsGrid.addEventListener('click', (e) => {
      const copyBtn = e.target.closest('[data-action="copy"]');
      const listBtn = e.target.closest('[data-action="list-for-sale"]');

      if (copyBtn) {
            const card = copyBtn.closest('.result-card');
            copyPayload(card, copyBtn);
      }

      if (listBtn) {
            const listingId = listBtn.dataset.listingId;
            listForSale(listingId);
      }
});

function showPreview() {
      previewGrid.innerHTML = '';
      photoCount.textContent = appState.getFileCount();

      appState.selectedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                  const previewItem = document.createElement('div');
                  previewItem.className = 'preview-item';
                  previewItem.setAttribute('role', 'listitem');
                  previewItem.innerHTML = `
                        <img src="${e.target.result}" alt="Preview of ${escapeHtml(file.name)}">
                        <button class="remove-btn" data-index="${index}" aria-label="Remove ${escapeHtml(file.name)}">×</button>
                  `;
                  previewGrid.appendChild(previewItem);
            };
            reader.readAsDataURL(file);
      });

      setSectionVisibility(previewSection, true);
      uploadBox.style.display = 'none';
      setSectionVisibility(errorSection, false);
}

function removeFile(index) {
      appState.removeFile(index);
      if (appState.getFileCount() === 0) {
            clearPreview();
      } else {
            showPreview();
      }
}

function clearPreview() {
      appState.clearFiles();
      photoInput.value = '';
      setSectionVisibility(previewSection, false);
      uploadBox.style.display = 'block';
      setSectionVisibility(errorSection, false);
}

async function submitForm() {
      if (appState.getFileCount() === 0) {
            showError('Please select at least one photo first.');
            return;
      }

      try {
            // Show loading state
            setSectionVisibility(previewSection, false);
            setSectionVisibility(loadingSection, true);
            setSectionVisibility(resultsSection, false);
            setSectionVisibility(errorSection, false);

            appState.clearResults();
            appState.setProcessing(true);
            const totalFiles = appState.getFileCount();

            // Process each file
            for (let i = 0; i < appState.selectedFiles.length; i++) {
                  const file = appState.selectedFiles[i];
                  updateProgress(i, totalFiles, `Processing ${i + 1} of ${totalFiles}...`);

                  const formData = new FormData();
                  formData.append('photo', file);

                  try {
                        const response = await fetch(`${API_BASE_URL}/api/upload`, {
                              method: 'POST',
                              body: formData
                        });

                        const data = await response.json();

                        if (!response.ok || !data.success) {
                              console.warn(`Failed to process ${file.name}:`, data.error);
                              appState.addResult({
                                    filename: file.name,
                                    success: false,
                                    error: data.error || 'Unknown error'
                              });
                        } else {
                              appState.addResult({
                                    filename: file.name,
                                    success: true,
                                    data: data
                              });
                        }
                  } catch (error) {
                        console.warn(`Error processing ${file.name}:`, error);
                        appState.addResult({
                              filename: file.name,
                              success: false,
                              error: error.message
                        });
                  }
            }

            // Display results
            appState.setProcessing(false);
            displayBatchResults();
            setSectionVisibility(loadingSection, false);
            setSectionVisibility(resultsSection, true);
            announceToScreenReaders(
                  `Processing complete. Generated ${appState.getSuccessfulResults().length} listing(s).`
            );

      } catch (error) {
            appState.setProcessing(false);
            console.error('Error:', error);
            showError('Batch processing failed: ' + error.message);
      }
}

function updateProgress(current, total, message) {
      const percentage = ((current + 1) / total) * 100;
      progressFill.style.width = percentage + '%';
      loadingProgress.textContent = message;

      // Update ARIA attributes
      const progressBar = document.querySelector('[role="progressbar"]');
      if (progressBar) {
            progressBar.setAttribute('aria-valuenow', Math.round(percentage));
      }
}

function displayBatchResults() {
      const successful = appState.getSuccessfulResults();
      const successCount = successful.length;
      resultCount.textContent = successCount;

      resultsGrid.innerHTML = '';

      const highValueCount = appState.getHighValueResults().length;
      notifyHighValueCards(highValueCount);

      appState.processedResults.forEach((result, index) => {
            if (result.success) {
                  const data = result.data;
                  // Normalized response: always an array of listings
                  const listings = Array.isArray(data.listings) ? data.listings : [data];
                  listings.forEach((listingItem, listingIndex) => {
                        const label = listings.length > 1
                              ? `${result.filename} (Card ${listingIndex + 1})`
                              : result.filename;
                        const card = createResultCard(listingItem, label);
                        resultsGrid.appendChild(card);
                  });
            } else {
                  const errorCard = createErrorCard(result.filename, result.error);
                  resultsGrid.appendChild(errorCard);
            }
      });
}

function createResultCard(data, filename) {
      const analysis = data.analysis;
      const listings = data.comparable_listings;
      const price = data.suggested_price;
      const isHighValue = data.is_high_value === true;

      const card = document.createElement('div');
      card.className = 'result-card';

      // Build features list
      let featuresList = '';
      if (analysis.features) {
            const features = Array.isArray(analysis.features) ? analysis.features : [analysis.features];
            featuresList = features.map(f => `<li>${escapeHtml(f)}</li>`).join('');
      }

      // Build grading notes
      let gradingNotes = '';
      if (analysis.grading_notes) {
            const notes = Array.isArray(analysis.grading_notes) ? analysis.grading_notes : [analysis.grading_notes];
            gradingNotes = `
                  <div style="margin: 10px 0;">
                        <p style="font-size: 0.85em; color: #666; margin: 0 0 6px 0;"><strong>Grading notes:</strong></p>
                        <ul style="margin: 0; padding-left: 20px; font-size: 0.85em;">${notes.map(n => `<li>${n}</li>`).join('')}</ul>
                  </div>
            `;
      }

      // Build listings table
      let listingsTable = '';
      if (listings && listings.length > 0) {
            const rows = listings.map(item => `
                  <tr>
                        <td style="font-size: 0.9em;">${escapeHtml(item.title || 'Unknown')}</td>
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
            ${isHighValue ? '<div class="high-value-badge">🔥 High Value</div>' : ''}
            <h3 style="margin: 0 0 15px 0; color: #333; word-break: break-word;">
                  📷 ${escapeHtml(filename)}
            </h3>
            <div style="background: #f0f0f0; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
                  <p style="margin: 4px 0; font-size: 0.9em;"><strong>${escapeHtml(analysis.brand || 'Unknown')} ${escapeHtml(analysis.model || '')}</strong></p>
                  <p style="margin: 4px 0; font-size: 0.85em; color: #666;">${escapeHtml(analysis.category || 'Unknown')}</p>
                  <p style="margin: 4px 0; font-size: 0.85em; color: #666;">Condition: ${escapeHtml(analysis.condition || 'Unknown')}</p>
            </div>
            ${featuresList ? `<ul style="margin: 10px 0; padding-left: 20px; font-size: 0.85em;">${featuresList}</ul>` : ''}
            ${gradingNotes}
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px; border-radius: 8px; text-align: center; margin: 15px 0;">
                  <p style="margin: 0; font-size: 0.85em; opacity: 0.9;">Suggested Price</p>
                  <p style="margin: 4px 0; font-size: 1.4em; font-weight: bold;">$${parseFloat(price).toFixed(2)}</p>
            </div>
            ${listingsTable}
            <div style="display:flex; gap:8px; margin-top:12px;">
                  <button class="btn-secondary" style="width: 100%;" data-action="copy" data-listing-id="${escapeHtml(String(data.listing_id || ''))}" aria-label="Copy eBay payload for ${escapeHtml(filename)}">📋 Copy Payload</button>
                  <button class="btn-primary" style="width: 100%;" data-action="list-for-sale" data-listing-id="${escapeHtml(String(data.listing_id || ''))}" aria-label="List ${escapeHtml(filename)} for sale on eBay">🛒 List for Sale</button>
            </div>
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
            <h3 style="margin: 0 0 10px 0; color: #f44336;">❌ ${escapeHtml(filename)}</h3>
            <p style="margin: 0; color: #c62828; font-size: 0.9em;">${escapeHtml(error)}</p>
      `;

      return card;
}

function copyPayload(card, btn) {
      const payload = card.dataset.payload;
      const button = btn || card.querySelector('[data-action="copy"]');

      navigator.clipboard.writeText(payload).then(() => {
            const originalText = button.textContent;
            button.textContent = '✓ Copied!';
            setTimeout(() => {
                  button.textContent = originalText;
            }, 2000);
      }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Failed to copy to clipboard');
      });
}

function downloadAllListings() {
      // Flatten all listing payloads from the normalized listings array
      const payloads = appState.getSuccessfulResults().flatMap(r => {
            const data = r.data;
            if (Array.isArray(data.listings)) {
                  return data.listings.map(l => l.payload).filter(Boolean);
            }
            return data.payload ? [data.payload] : [];
      });

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
      setSectionVisibility(errorSection, true);
      setSectionVisibility(loadingSection, false);
      setSectionVisibility(previewSection, false);
      setSectionVisibility(resultsSection, false);
}

function resetForm() {
      clearPreview();
      setSectionVisibility(resultsSection, false);
      setSectionVisibility(loadingSection, false);
      appState.clearResults();
      progressFill.style.width = '0%';
      const progressBar = document.querySelector('[role="progressbar"]');
      if (progressBar) progressBar.setAttribute('aria-valuenow', '0');
}

// Auto-focus on page load
window.addEventListener('load', () => {
      uploadBox.focus();
      updateEbayConnectionUI();

      // Register PWA service worker
      if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js').catch((err) => {
                  console.warn('Service worker registration failed:', err);
            });
      }
});
