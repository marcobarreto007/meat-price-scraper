/**
 * MeatPrice Tracker - Client-side JavaScript
 * Handles language switching, API calls, and dynamic content
 */

// Language management
const LANG_STORAGE_KEY = 'meatprice_lang';

function getCurrentLang() {
    return localStorage.getItem(LANG_STORAGE_KEY) || 'en';
}

function setLanguage(lang) {
    localStorage.setItem(LANG_STORAGE_KEY, lang);
    document.cookie = `lang=${lang}; path=/; max-age=31536000`;
    
    // Update UI
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
    
    // Reload page to apply new language
    window.location.reload();
}

// Initialize language buttons
document.addEventListener('DOMContentLoaded', () => {
    const currentLang = getCurrentLang();
    
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            setLanguage(btn.dataset.lang);
        });
    });
});

// API helper functions
const API_BASE = '/api';

async function fetchAPI(endpoint, params = {}) {
    const lang = getCurrentLang();
    const url = new URL(`${API_BASE}${endpoint}`, window.location.origin);
    
    if (lang) {
        url.searchParams.set('lang', lang);
    }
    
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            url.searchParams.set(key, value);
        }
    });
    
    try {
        const response = await fetch(url.toString());
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API fetch error:', error);
        throw error;
    }
}

// Format currency
function formatCurrency(amount, currency = 'CAD') {
    return new Intl.NumberFormat('en-CA', {
        style: 'currency',
        currency: currency,
    }).format(amount);
}

// Format date
function formatDate(dateString, lang = 'en') {
    const date = new Date(dateString);
    const locale = lang === 'fr' ? 'fr-CA' : 'en-CA';
    
    return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(date);
}

// Render price table
function renderPriceTable(containerId, prices, t) {
    const container = document.getElementById(containerId);
    if (!container || !prices || prices.length === 0) {
        if (container) {
            container.innerHTML = `<p class="text-center text-gray-500">${t.no_results}</p>`;
        }
        return;
    }
    
    // Sort by unit_price or price_cad
    const sorted = [...prices].sort((a, b) => {
        const aPrice = a.unit_price || a.price_cad;
        const bPrice = b.unit_price || b.price_cad;
        return aPrice - bPrice;
    });
    
    let html = `
        <div class="price-table-container">
            <table class="price-table">
                <thead>
                    <tr>
                        <th>${t.th_rank}</th>
                        <th>${t.th_store_product}</th>
                        <th>${t.th_price_kg}</th>
                        <th>${t.th_price}</th>
                        <th>${t.th_sale}</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    sorted.forEach((price, index) => {
        const rank = index + 1;
        const rankClass = rank <= 3 ? 'rank-cell' : 'rank-cell';
        const saleBadge = price.is_on_sale 
            ? `<span class="badge badge-sale">${t.sale_yes}</span>` 
            : '';
        
        html += `
            <tr>
                <td class="${rankClass}">${rank}</td>
                <td class="store-cell">
                    <div>${price.store_name || price.store_id}</div>
                    <div class="product-detail">${price.product_name || ''}</div>
                </td>
                <td class="price-kg">
                    ${price.unit_price ? formatCurrency(price.unit_price) + t.per_kg : '—'}
                </td>
                <td class="price-total">${formatCurrency(price.price_cad)}</td>
                <td class="sale-cell">${saleBadge}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Load products with prices
async function loadProductsPage() {
    const lang = getCurrentLang();
    
    try {
        const [productsData, pricesData] = await Promise.all([
            fetchAPI('/products'),
            fetchAPI('/prices'),
        ]);
        
        const productNames = {};
        productsData.products.forEach(p => {
            productNames[p.slug] = p.name;
        });
        
        // Group prices by product
        const pricesByProduct = {};
        pricesData.prices.forEach(price => {
            if (!pricesByProduct[price.product_slug]) {
                pricesByProduct[price.product_slug] = [];
            }
            pricesByProduct[price.product_slug].push(price);
        });
        
        // Render each product section
        Object.keys(productNames).forEach(slug => {
            const container = document.getElementById(`product-${slug}`);
            if (!container) return;
            
            const prices = pricesByProduct[slug] || [];
            const topPrices = prices.slice(0, 5);
            
            let html = `
                <div class="product-card fade-in">
                    <div class="product-header">
                        <svg class="product-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19.5 9C19.5 9 21 10.5 21 13C21 15.5 19 17 17 17C15 17 14.5 15.5 13 15.5C11.5 15.5 11 17 9 17C7 17 4.5 15.5 4.5 12.5C4.5 9.5 7 7 9.5 7C12 7 13.5 8 14.5 8C15.5 8 17 7.5 17 6C17 4.5 16 3.5 14.5 3.5C13 3.5 12 4.5 12 4.5"/>
                        </svg>
                        <h3 class="product-name">${productNames[slug]}</h3>
                    </div>
                    <div class="product-body">
                        <ul class="price-list">
            `;
            
            topPrices.forEach(price => {
                const saleBadge = price.is_on_sale 
                    ? `<span class="sale-badge">SALE</span>` 
                    : '';
                
                html += `
                    <li class="price-item">
                        <div>
                            <span class="price-store">${price.store_name}</span>
                            ${saleBadge}
                        </div>
                        <div>
                            <span class="price-value">${formatCurrency(price.price_cad)}</span>
                            ${price.unit_price ? `<span class="price-unit">(${formatCurrency(price.unit_price)}/kg)</span>` : ''}
                        </div>
                    </li>
                `;
            });
            
            if (topPrices.length === 0) {
                html += `<li class="price-item"><span class="text-gray-500">No prices available</span></li>`;
            }
            
            html += `
                        </ul>
                    </div>
                </div>
            `;
            
            container.innerHTML = html;
        });
        
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

// Load history page
async function loadHistoryPage() {
    const productSelect = document.getElementById('history-product');
    const daysSelect = document.getElementById('history-days');
    const resultsContainer = document.getElementById('history-results');
    
    if (!productSelect || !daysSelect || !resultsContainer) return;
    
    // Load products into select
    try {
        const productsData = await fetchAPI('/products');
        
        productsData.products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.slug;
            option.textContent = product.name;
            productSelect.appendChild(option);
        });
        
        // Load initial history
        await loadHistory(productsData.products[0]?.slug, 30);
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
    
    // Event listeners
    productSelect.addEventListener('change', () => {
        loadHistory(productSelect.value, daysSelect.value);
    });
    
    daysSelect.addEventListener('change', () => {
        loadHistory(productSelect.value, daysSelect.value);
    });
}

async function loadHistory(productSlug, days) {
    const resultsContainer = document.getElementById('history-results');
    const lang = getCurrentLang();
    
    if (!resultsContainer || !productSlug) return;
    
    resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        const data = await fetchAPI(`/history/${productSlug}`, { days });
        
        if (data.prices.length === 0) {
            resultsContainer.innerHTML = `<p class="text-center text-gray-500">No history found</p>`;
            return;
        }
        
        renderPriceTable('history-results', data.prices, {
            no_results: 'No results found',
            th_rank: '#',
            th_store_product: 'Store / Product',
            th_price_kg: 'Price/kg',
            th_price: 'Price',
            th_sale: 'Sale',
            sale_yes: lang === 'fr' ? 'OUI' : 'YES',
        });
        
    } catch (error) {
        console.error('Error loading history:', error);
        resultsContainer.innerHTML = '<p class="text-center text-red-500">Error loading history</p>';
    }
}

// Export for use in templates
window.MeatPriceTracker = {
    getCurrentLang,
    setLanguage,
    fetchAPI,
    formatCurrency,
    formatDate,
    renderPriceTable,
    loadProductsPage,
    loadHistoryPage,
    loadHistory,
};

// Auto-initialize based on page
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('product-chicken_breast')) {
        loadProductsPage();
    }
    
    if (document.getElementById('history-product')) {
        loadHistoryPage();
    }
});
