/**
 * AppState - Centralized state management for Cards-4-Sale
 * Single source of truth for all application state
 */

class AppState {
    constructor() {
        this.selectedFiles = [];
        this.processedResults = [];
        this.ebayConnected = false;
        this.currentTab = 'upload';
        this.isProcessing = false;
        this.error = null;
        this.lastActivity = new Date();

        // Listeners for state changes
        this.listeners = new Set();

        // Restore from localStorage if available
        this.restore();
    }

    /**
     * Add listener to state changes
     * @param {Function} listener - Callback function
     */
    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    /**
     * Notify all listeners of state change
     * @param {string} key - Property that changed
     * @param {*} newValue - New value
     */
    notify(key, newValue) {
        this.lastActivity = new Date();
        this.listeners.forEach(listener => {
            listener({ key, newValue, state: this });
        });
    }

    // FILES MANAGEMENT

    /**
     * Add files to selection
     * @param {File[]} files - File objects
     */
    addFiles(files) {
        this.selectedFiles = Array.from(files);
        this.notify('selectedFiles', this.selectedFiles);
    }

    /**
     * Remove specific file
     * @param {number} index - File index
     */
    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.notify('selectedFiles', this.selectedFiles);
    }

    /**
     * Clear all selected files
     */
    clearFiles() {
        this.selectedFiles = [];
        this.notify('selectedFiles', []);
    }

    /**
     * Get file count
     */
    getFileCount() {
        return this.selectedFiles.length;
    }

    // RESULTS MANAGEMENT

    /**
     * Add processing result
     * @param {Object} result - Result object {success, data, filename, error}
     */
    addResult(result) {
        this.processedResults.push(result);
        this.notify('processedResults', this.processedResults);
    }

    /**
     * Get successful results only
     */
    getSuccessfulResults() {
        return this.processedResults.filter(r => r.success);
    }

    /**
     * Get high-value results
     */
    getHighValueResults() {
        return this.getSuccessfulResults()
            .filter(r => r.data?.is_high_value === true);
    }

    /**
     * Clear all results
     */
    clearResults() {
        this.processedResults = [];
        this.notify('processedResults', []);
    }

    /**
     * Get result by index
     */
    getResult(index) {
        return this.processedResults[index];
    }

    /**
     * Get result count
     */
    getResultCount() {
        return this.processedResults.length;
    }

    // CONNECTION STATE

    /**
     * Set eBay connection state
     * @param {boolean} connected
     */
    setEbayConnected(connected) {
        this.ebayConnected = connected;
        this.notify('ebayConnected', connected);
    }

    /**
     * Check if eBay is connected
     */
    isEbayConnected() {
        return this.ebayConnected;
    }

    // PROCESSING STATE

    /**
     * Set processing state
     * @param {boolean} processing
     */
    setProcessing(processing) {
        this.isProcessing = processing;
        this.notify('isProcessing', processing);
    }

    /**
     * Check if currently processing
     */
    isCurrentlyProcessing() {
        return this.isProcessing;
    }

    // ERROR STATE

    /**
     * Set error message
     * @param {string|null} error
     */
    setError(error) {
        this.error = error;
        this.notify('error', error);
    }

    /**
     * Get current error
     */
    getError() {
        return this.error;
    }

    /**
     * Clear error
     */
    clearError() {
        this.error = null;
        this.notify('error', null);
    }

    // TAB NAVIGATION

    /**
     * Switch to tab
     * @param {string} tabName
     */
    switchTab(tabName) {
        this.currentTab = tabName;
        this.notify('currentTab', tabName);
    }

    /**
     * Get current tab
     */
    getCurrentTab() {
        return this.currentTab;
    }

    // PERSISTENCE

    /**
     * Save state to localStorage
     */
    persist() {
        const persistable = {
            ebayConnected: this.ebayConnected,
            currentTab: this.currentTab,
        };
        localStorage.setItem('appState', JSON.stringify(persistable));
    }

    /**
     * Restore state from localStorage
     */
    restore() {
        const saved = localStorage.getItem('appState');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                this.ebayConnected = data.ebayConnected || false;
                this.currentTab = data.currentTab || 'upload';
            } catch (e) {
                console.error('Failed to restore state:', e);
            }
        }
    }

    // SERIALIZATION (for debugging)

    /**
     * Get summary of state
     */
    serialize() {
        return {
            filesSelected: this.selectedFiles.length,
            resultsProcessed: this.processedResults.length,
            successfulResults: this.getSuccessfulResults().length,
            highValueCards: this.getHighValueResults().length,
            ebayConnected: this.ebayConnected,
            currentTab: this.currentTab,
            isProcessing: this.isProcessing,
            hasError: !!this.error,
        };
    }

    /**
     * Log state for debugging
     */
    debug() {
        console.log('📊 AppState:', this.serialize());
        console.log('📋 Files:', this.selectedFiles);
        console.log('📦 Results:', this.processedResults);
    }

    // LIFECYCLE

    /**
     * Reset entire state
     */
    reset() {
        this.selectedFiles = [];
        this.processedResults = [];
        this.isProcessing = false;
        this.error = null;
        this.clearResults();
        this.clearFiles();
        this.clearError();
    }
}

// Global instance
const appState = new AppState();

// Save state before unload
window.addEventListener('beforeunload', () => {
    appState.persist();
});
