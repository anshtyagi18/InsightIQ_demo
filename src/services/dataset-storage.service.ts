/**
 * Dataset Storage Service
 * Provides full persistence for uploaded & processed datasets in IndexedDB and localStorage.
 * Enables datasets to be saved, cleaned, reopened, and set as active across the entire platform.
 */

import { DatasetProfile, profileDataset, cleanDataset } from './bi-engine';

export interface CleaningHistoryItem {
  id: string;
  timestamp: string;
  action: string;
  details: string;
}

export interface SavedDataset {
  id: string;
  name: string;
  filename: string;
  sizeBytes: number;
  rowCount: number;
  columnCount: number;
  columns: string[];
  rawRows: Record<string, any>[];
  cleanedRows: Record<string, any>[];
  profile: DatasetProfile;
  createdAt: string;
  updatedAt: string;
  cleaningHistory: CleaningHistoryItem[];
  isActive?: boolean;
}

const STORAGE_KEY_DATASETS = 'insightiq_saved_datasets_v1';
const STORAGE_KEY_ACTIVE_ID = 'insightiq_active_dataset_id_v1';

// Initial Sample Datasets to populate if store is empty
const INITIAL_SAMPLES: Omit<SavedDataset, 'id' | 'createdAt' | 'updatedAt'>[] = [
  {
    name: 'Q3 Sales & Revenue Data',
    filename: 'q3_sales_revenue.csv',
    sizeBytes: 15420,
    rowCount: 20,
    columnCount: 6,
    columns: ['Date', 'Region', 'Category', 'Sales', 'Units_Sold', 'Profit'],
    rawRows: [
      { Date: '2024-07-01', Region: 'North', Category: 'Electronics', Sales: 12500, Units_Sold: 45, Profit: 3200 },
      { Date: '2024-07-02', Region: 'South', Category: 'Furniture', Sales: 8400, Units_Sold: 28, Profit: 1800 },
      { Date: '2024-07-03', Region: 'East', Category: 'Electronics', Sales: 15600, Units_Sold: 52, Profit: 4100 },
      { Date: '2024-07-04', Region: 'West', Category: 'Clothing', Sales: 6200, Units_Sold: 80, Profit: 1500 },
      { Date: '2024-07-05', Region: 'North', Category: 'Furniture', Sales: 9800, Units_Sold: 32, Profit: 2200 },
      { Date: '2024-07-06', Region: 'South', Category: 'Electronics', Sales: 18200, Units_Sold: 60, Profit: 5400 },
      { Date: '2024-07-07', Region: 'East', Category: 'Clothing', Sales: 7500, Units_Sold: 95, Profit: 1900 },
      { Date: '2024-07-08', Region: 'West', Category: 'Electronics', Sales: 14100, Units_Sold: 48, Profit: 3800 },
      { Date: '2024-07-09', Region: 'North', Category: 'Clothing', Sales: 8900, Units_Sold: 110, Profit: 2100 },
      { Date: '2024-07-10', Region: 'South', Category: 'Furniture', Sales: 11200, Units_Sold: 38, Profit: 2700 },
      { Date: '2024-07-11', Region: 'East', Category: 'Electronics', Sales: 16800, Units_Sold: 55, Profit: 4600 },
      { Date: '2024-07-12', Region: 'West', Category: 'Furniture', Sales: 7900, Units_Sold: 25, Profit: 1600 },
      { Date: '2024-07-13', Region: 'North', Category: 'Electronics', Sales: 13400, Units_Sold: 46, Profit: 3500 },
      { Date: '2024-07-14', Region: 'South', Category: 'Clothing', Sales: 9100, Units_Sold: 115, Profit: 2300 },
      { Date: '2024-07-15', Region: 'East', Category: 'Furniture', Sales: 10500, Units_Sold: 34, Profit: 2400 },
      { Date: '2024-07-16', Region: 'West', Category: 'Electronics', Sales: 19500, Units_Sold: 64, Profit: 5800 },
      { Date: '2024-07-17', Region: 'North', Category: 'Furniture', Sales: 8700, Units_Sold: 29, Profit: 1950 },
      { Date: '2024-07-18', Region: 'South', Category: 'Electronics', Sales: 14800, Units_Sold: 50, Profit: 3900 },
      { Date: '2024-07-19', Region: 'East', Category: 'Clothing', Sales: 8200, Units_Sold: 102, Profit: 2050 },
      { Date: '2024-07-20', Region: 'West', Category: 'Furniture', Sales: 12100, Units_Sold: 40, Profit: 2900 },
    ],
    get cleanedRows() { return this.rawRows; },
    get profile() { return profileDataset(this.rawRows); },
    cleaningHistory: [
      { id: '1', timestamp: new Date().toISOString(), action: 'Import', details: 'Sample Q3 Sales dataset loaded' }
    ]
  },
  {
    name: 'Customer Churn & Retention Metrics',
    filename: 'customer_churn.csv',
    sizeBytes: 12100,
    rowCount: 15,
    columnCount: 6,
    columns: ['CustomerID', 'Plan', 'Tenure_Months', 'MonthlySpend', 'SupportTickets', 'Churned'],
    rawRows: [
      { CustomerID: 'CUST-101', Plan: 'Premium', Tenure_Months: 24, MonthlySpend: 149.99, SupportTickets: 1, Churned: 'No' },
      { CustomerID: 'CUST-102', Plan: 'Basic', Tenure_Months: 3, MonthlySpend: 29.99, SupportTickets: 5, Churned: 'Yes' },
      { CustomerID: 'CUST-103', Plan: 'Pro', Tenure_Months: 12, MonthlySpend: 79.99, SupportTickets: 2, Churned: 'No' },
      { CustomerID: 'CUST-104', Plan: 'Basic', Tenure_Months: 1, MonthlySpend: 29.99, SupportTickets: 7, Churned: 'Yes' },
      { CustomerID: 'CUST-105', Plan: 'Premium', Tenure_Months: 36, MonthlySpend: 149.99, SupportTickets: 0, Churned: 'No' },
      { CustomerID: 'CUST-106', Plan: 'Pro', Tenure_Months: 8, MonthlySpend: 79.99, SupportTickets: 4, Churned: 'Yes' },
      { CustomerID: 'CUST-107', Plan: 'Enterprise', Tenure_Months: 18, MonthlySpend: 499.99, SupportTickets: 2, Churned: 'No' },
      { CustomerID: 'CUST-108', Plan: 'Basic', Tenure_Months: 5, MonthlySpend: 29.99, SupportTickets: 3, Churned: 'No' },
      { CustomerID: 'CUST-109', Plan: 'Pro', Tenure_Months: 2, MonthlySpend: 79.99, SupportTickets: 6, Churned: 'Yes' },
      { CustomerID: 'CUST-110', Plan: 'Enterprise', Tenure_Months: 48, MonthlySpend: 499.99, SupportTickets: 1, Churned: 'No' },
      { CustomerID: 'CUST-111', Plan: 'Premium', Tenure_Months: 15, MonthlySpend: 149.99, SupportTickets: 3, Churned: 'No' },
      { CustomerID: 'CUST-112', Plan: 'Basic', Tenure_Months: 4, MonthlySpend: 29.99, SupportTickets: 8, Churned: 'Yes' },
      { CustomerID: 'CUST-113', Plan: 'Pro', Tenure_Months: 20, MonthlySpend: 79.99, SupportTickets: 1, Churned: 'No' },
      { CustomerID: 'CUST-114', Plan: 'Premium', Tenure_Months: 9, MonthlySpend: 149.99, SupportTickets: 5, Churned: 'Yes' },
      { CustomerID: 'CUST-115', Plan: 'Enterprise', Tenure_Months: 30, MonthlySpend: 499.99, SupportTickets: 0, Churned: 'No' },
    ],
    get cleanedRows() { return this.rawRows; },
    get profile() { return profileDataset(this.rawRows); },
    cleaningHistory: [
      { id: '1', timestamp: new Date().toISOString(), action: 'Import', details: 'Sample Customer Churn dataset loaded' }
    ]
  }
];

class DatasetStorageService {
  private memoryCache: SavedDataset[] | null = null;

  /**
   * Initialize and get all saved datasets
   */
  async getAllDatasets(): Promise<SavedDataset[]> {
    if (this.memoryCache) {
      return this.memoryCache;
    }

    try {
      const stored = localStorage.getItem(STORAGE_KEY_DATASETS);
      if (stored !== null) {
        const parsed: SavedDataset[] = JSON.parse(stored);
        this.memoryCache = parsed;
        return parsed;
      }
    } catch (err) {
      console.warn('Failed to parse saved datasets from localStorage:', err);
    }

    // Seed initial samples if empty
    const seeded = INITIAL_SAMPLES.map((sample, idx) => {
      const now = new Date().toISOString();
      return {
        ...sample,
        id: `dataset_sample_${idx + 1}_${Date.now()}`,
        createdAt: now,
        updatedAt: now,
        isActive: idx === 0,
      } as SavedDataset;
    });

    this.saveToStorage(seeded);
    if (seeded.length > 0) {
      this.setActiveDataset(seeded[0].id);
    }
    this.memoryCache = seeded;
    return seeded;
  }

  /**
   * Get dataset by ID
   */
  async getDatasetById(id: string): Promise<SavedDataset | null> {
    const datasets = await this.getAllDatasets();
    return datasets.find(d => d.id === id) || null;
  }

  /**
   * Save a new dataset
   */
  async saveDataset(item: Omit<SavedDataset, 'id' | 'createdAt' | 'updatedAt'>): Promise<SavedDataset> {
    const datasets = await this.getAllDatasets();
    const now = new Date().toISOString();
    const newId = `dataset_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;

    const newDataset: SavedDataset = {
      ...item,
      id: newId,
      createdAt: now,
      updatedAt: now,
      cleanedRows: item.cleanedRows || item.rawRows,
      profile: profileDataset(item.cleanedRows || item.rawRows),
      cleaningHistory: item.cleaningHistory || [
        { id: '1', timestamp: now, action: 'Upload', details: `Uploaded ${item.filename}` }
      ],
      isActive: false
    };

    const updatedList = [newDataset, ...datasets];
    this.saveToStorage(updatedList);
    this.memoryCache = updatedList;

    // Automatically set as active if it's the only dataset or user uploaded it
    await this.setActiveDataset(newId);

    return newDataset;
  }

  /**
   * Update dataset (e.g. after cleaning)
   */
  async updateDataset(id: string, updates: Partial<SavedDataset>, historyLog?: { action: string; details: string }): Promise<SavedDataset | null> {
    const datasets = await this.getAllDatasets();
    const index = datasets.findIndex(d => d.id === id);
    if (index === -1) return null;

    const existing = datasets[index];
    const now = new Date().toISOString();

    const newHistory = [...existing.cleaningHistory];
    if (historyLog) {
      newHistory.unshift({
        id: `hist_${Date.now()}`,
        timestamp: now,
        action: historyLog.action,
        details: historyLog.details
      });
    }

    const updatedRows = updates.cleanedRows || existing.cleanedRows;
    const updatedProfile = profileDataset(updatedRows);

    const updatedDataset: SavedDataset = {
      ...existing,
      ...updates,
      cleanedRows: updatedRows,
      rowCount: updatedRows.length,
      columnCount: updatedProfile.columnCount,
      columns: updatedProfile.columns.map(c => c.name),
      profile: updatedProfile,
      updatedAt: now,
      cleaningHistory: newHistory
    };

    datasets[index] = updatedDataset;
    this.saveToStorage(datasets);
    this.memoryCache = datasets;

    return updatedDataset;
  }

  /**
   * Delete dataset by ID
   */
  async deleteDataset(id: string): Promise<boolean> {
    const datasets = await this.getAllDatasets();
    const filtered = datasets.filter(d => d.id !== id);
    if (filtered.length === datasets.length) return false;

    this.saveToStorage(filtered);
    this.memoryCache = filtered;

    // If deleted dataset was active, activate the first remaining dataset
    const activeId = localStorage.getItem(STORAGE_KEY_ACTIVE_ID);
    if (activeId === id) {
      if (filtered.length > 0) {
        await this.setActiveDataset(filtered[0].id);
      } else {
        localStorage.removeItem(STORAGE_KEY_ACTIVE_ID);
      }
    }

    return true;
  }

  /**
   * Get active dataset
   */
  async getActiveDataset(): Promise<SavedDataset | null> {
    const datasets = await this.getAllDatasets();
    if (datasets.length === 0) return null;

    const activeId = localStorage.getItem(STORAGE_KEY_ACTIVE_ID);
    if (activeId) {
      const found = datasets.find(d => d.id === activeId);
      if (found) return found;
    }

    // Default to first dataset
    await this.setActiveDataset(datasets[0].id);
    return datasets[0];
  }

  /**
   * Set active dataset ID
   */
  async setActiveDataset(id: string): Promise<SavedDataset | null> {
    const datasets = await this.getAllDatasets();
    const target = datasets.find(d => d.id === id);
    if (!target) return null;

    localStorage.setItem(STORAGE_KEY_ACTIVE_ID, id);

    // Update active flag on list
    const updatedList = datasets.map(d => ({
      ...d,
      isActive: d.id === id
    }));

    this.saveToStorage(updatedList);
    this.memoryCache = updatedList;

    return target;
  }

  private saveToStorage(datasets: SavedDataset[]): void {
    try {
      localStorage.setItem(STORAGE_KEY_DATASETS, JSON.stringify(datasets));
    } catch (err) {
      console.warn('Failed to store datasets to localStorage:', err);
    }
  }
}

export const datasetStorage = new DatasetStorageService();
export default datasetStorage;
