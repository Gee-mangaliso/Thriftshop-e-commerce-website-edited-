// Backend Connector for Mzansi Thrift Store
class BackendConnector {
    constructor() {
        this.baseURL = 'http://127.0.0.1:5000/api';
//        this.token = localStorage.getItem('authToken');
    }
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            ...options
        };

        console.log("📡 Sending request to:", url);
        console.log("🧾 Config:", config);

        // Add timeout
        const timeout = 50000; // 50 seconds
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        config.signal = controller.signal;
        try {
            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            if (response.status === 401) {
                    showPage('login');
                    throw new Error('Authentication required');
                }

            if (response.status === 403) {
                throw new Error('Access forbidden');
            }
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const text = await response.text();
                console.error("❌ Unexpected response format:", text);
                throw new Error(`Unexpected response format: ${text}`);
            }
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `Request failed with status ${response.status}`);
            }

            return data;
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout. Please try again.');
            }
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Authentication Methods
    async register(userData) {
        try {
        console.log("🚀 Calling register() with:", userData);
            const data = await this.request('/register', {
                method: 'POST',
                headers: {
                   'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });
             console.log("✅ Response from backend:", data);
             return data;

        } catch (error) {
            throw new Error(`Registration failed: ${error.message}`);
        }
    }
    async seller_register(sellerData) {
            try {
            console.log("🚀 Calling register() with:", sellerData);
                const data = await this.request('/seller/register', {
                    method: 'POST',
                    headers: {
                       'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(sellerData)
                });
                 console.log("✅ Response from backend:", data);
                 return data;

            } catch (error) {
                throw new Error(`Registration failed: ${error.message}`);
            }
        }

    async login(credentials) {
        try {
            const data = await this.request('/login', {
                method: 'POST',
                 headers: {
                      'Content-Type': 'application/json'
                 },
                body: JSON.stringify(credentials)
            });
            return data;

        } catch (error) {
            throw new Error(`Login failed: ${error.message}` || 'login failed');
        }
    }
    async seller_login(sellerCredentials) {
            try {
                const data = await this.request('/seller/login', {
                    method: 'POST',
                     headers: {
                          'Content-Type': 'application/json'
                     },
                    body: JSON.stringify(sellerCredentials)
                });
                return data;

            } catch (error) {
                throw new Error(`Login failed: ${error.message}` || 'login failed');
            }
        }

    async logout() {
        try {
            await this.request('/logout', {
                method: 'POST'
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.token = null;
        }
    }

    async getCurrentUser() {
        return this.request('/user');
    }

    // Product Methods
    async getProducts(filters = {}) {
        const params = new URLSearchParams();

        Object.keys(filters).forEach(key => {
            if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
                if (Array.isArray(filters[key])) {
                    filters[key].forEach(value => params.append(`${key}[]`, value));
                } else {
                    params.append(key, filters[key]);
                }
            }
        });

        const queryString = params.toString();
        const endpoint = queryString ? `/products?${queryString}` : '/products';

        return this.request(endpoint);
    }

    async getProduct(productId) {
        return this.request(`/products/${productId}`);
    }

    async createProduct(productData) {
        return this.request('/seller/products', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
    }

    async updateProduct(productId, productData) {
        return this.request(`/seller/products/${productId}`, {
            method: 'PUT',
            body: JSON.stringify(productData)
        });
    }

    async deleteProduct(productId) {
        return this.request(`/seller/products/${productId}`, {
            method: 'DELETE'
        });
    }

    // Cart Methods
    async getCart() {
        return this.request('/cart');
    }

    async addToCart(productId, quantity = 1) {
        return this.request('/cart', {
            method: 'POST',
            body: JSON.stringify({ product_id: productId, quantity })
        });
    }

    async updateCartItem(productId, quantity) {
        return this.request(`/cart/${productId}`, {
            method: 'PUT',
            body: JSON.stringify({ quantity })
        });
    }

    async removeFromCart(productId) {
        return this.request(`/cart?product_id=${productId}`, {
            method: 'DELETE'
        });
    }

    async clearCart() {
        return this.request('/cart', {
            method: 'DELETE'
        });
    }

    // Order Methods
    async getOrders() {
        return this.request('/orders');
    }

    async getOrder(orderId) {
        return this.request(`/orders/${orderId}`);
    }

    async createOrder(orderData) {
        return this.request('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    async cancelOrder(orderId) {
        return this.request(`/orders/${orderId}/cancel`, {
            method: 'POST'
        });
    }

    async updateOrderStatus(orderId, status) {
        return this.request(`/seller/orders/${orderId}`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    }

    // Payment Methods
    async processPayment(paymentData) {
        return this.request('/payments/process', {
            method: 'POST',
            body: JSON.stringify(paymentData)
        });
    }

    // Seller Methods
    async getSellerDashboard() {
        return this.request('/seller/dashboard');
    }

    async getSellerProducts() {
        return this.request('/seller/products');
    }

    async getSellerOrders() {
        return this.request('/seller/orders');
    }

    async getSellerStats() {
        return this.request('/seller/stats');
    }

    // Category Methods
    async getCategories() {
        return this.request('/categories');
    }

    // Review Methods
    async getProductReviews(productId) {
        return this.request(`/products/${productId}/reviews`);
    }

    async createReview(productId, reviewData) {
        return this.request(`/products/${productId}/reviews`, {
            method: 'POST',
            body: JSON.stringify(reviewData)
        });
    }

    // Media Upload Methods
    async uploadMedia(files) {
        const formData = new FormData();

        for (let i = 0; i < files.length; i++) {
            formData.append('media', files[i]);
        }

        try {
           const response = await fetch(`${this.baseURL}/upload-media`, {
               method: 'POST',
               credentials: 'include',
               body: formData
           });


            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Upload failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Media upload failed:', error);
            throw error;
        }
    }

    // User Profile Methods
    async updateProfile(profileData) {
        return this.request('/user/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }

    async updateAddress(addressData) {
        return this.request('/user/address', {
            method: 'PUT',
            body: JSON.stringify(addressData)
        });
    }

    async changePassword(passwordData) {
        return this.request('/user/password', {
            method: 'PUT',
            body: JSON.stringify(passwordData)
        });
    }

    // Contact Methods
    async sendContactMessage(messageData) {
        return this.request('/contact', {
            method: 'POST',
            body: JSON.stringify(messageData)
        });
    }
}

// South African Utilities
const SAUtils = {
    provinces: [
        'Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal',
        'Limpopo', 'Mpumalanga', 'North West', 'Northern Cape', 'Western Cape'
    ],

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-ZA', {
            style: 'currency',
            currency: 'ZAR'
        }).format(amount);
    },

    validateSAID(idNumber) {
        if (!idNumber || idNumber.length !== 13) return false;
        return /^\d{13}$/.test(idNumber);
    },

    validatePhone(phone) {
        const cleaned = phone.replace(/\s/g, '');
        return /^(\+27|0)[1-9][0-9]{8}$/.test(cleaned);
    },

    formatPhone(phone) {
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.startsWith('0')) {
            return `+27${cleaned.substring(1)}`;
        }
        return cleaned.startsWith('+') ? cleaned : `+27${cleaned}`;
    },

    calculateShipping(province, weight = 1) {
        const baseCosts = {
            'Gauteng': 65.00,
            'Western Cape': 85.00,
            'KwaZulu-Natal': 95.00,
            'Eastern Cape': 105.00,
            'Free State': 90.00,
            'Limpopo': 110.00,
            'Mpumalanga': 100.00,
            'North West': 95.00,
            'Northern Cape': 120.00
        };
        return (baseCosts[province] || 85.00) + (weight * 2.5);
    }
};

// Global API instance
    const api = new BackendConnector();

    // Restore user from localStorage on page load
    state.currentUser = null;
    state.currentSeller = null;

//    document.addEventListener('DOMContentLoaded', () => {
//        const savedUser = localStorage.getItem('currentUser');
//        if (savedUser) {
//            state.currentUser = JSON.parse(savedUser);
//        }
//        updateAuthUI();
//        showInitialPage();
//    });
    document.addEventListener('DOMContentLoaded', () => {
        const savedUser = localStorage.getItem('currentUser');
        const savedSeller = localStorage.getItem('currentSeller');

        state.currentUser = savedUser ? JSON.parse(savedUser) : null;
        state.currentSeller = savedSeller ? JSON.parse(savedSeller) : null;

//        updateAuthUI();
        showInitialPage();
    });


    function showInitialPage() {
      showPage('home');
// ============== state user logged in ===========//
      if (state.currentUser) {
        showPage('home');
        updateAuthUI();
      }else if(state.currentSeller){
// ========= state buyer logged in ==========//
         showPage('seller-dashboard');
         updateAuthUI();
         closeSellerModal();
      }
    }

// =========  Seller Modal =========
function showSellerModal() {
  const sellerModal = document.getElementById('sellerModal');
  if (sellerModal) {
    sellerModal.classList.remove('hidden');   // remove hidden class
    sellerModal.style.display = 'block';      // make it visible
  }
}

function closeSellerModal() {
  const sellerModal = document.getElementById('sellerModal');
  if (sellerModal) {
    sellerModal.classList.add('hidden');      // add hidden class back
    sellerModal.style.display = 'none';       // hide it
  }
}


    function requireAuth(pageId) {
        if (!state.currentUser) {
            alert('Please login first');
            showPage('login');
            return;
        }
        if(!state.currentSeller){
            alert('Please login first');
            showPage('login');
            return;
        }
        showPage(pageId);
    }
// Error handler for API calls
function handleApiError(error) {
    console.error('API Error:', error);

    if (error.message.includes('Network') || error.message.includes('Failed to fetch')) {
        showAlert('Network error. Please check your connection and try again.', 'error');
    } else if (error.message.includes('timeout')) {
        showAlert('Request timeout. Please try again.', 'error');
    } else if (error.message.includes('Authentication')) {
        showAlert('Please login to continue.', 'error');
        showPage('login');
    } else {
        showAlert(error.message || 'An error occurred. Please try again.', 'error');
    }
}

// Update the existing frontend functions to use the backend connector
function updateAuthUI() {
  console.log("updateAuthUI called, currentUser:", state.currentUser);
  console.log("updateAuthUI called, currentSeller:", state.currentSeller);

  const userDropdown = document.getElementById('userDropdown');
  const userName = document.getElementById('userName');
  const sellerName = document.getElementById('sellerName');
  const loginButton = document.getElementById('loginBtn');
  const registerBtn = document.getElementById('registerBtn');
  const logoutButton = document.getElementById('logoutBtn');
  const userMenuBtn = document.getElementById('userMenuBtn');
  const userMenu = document.querySelector('.user-menu');

//    console.log("userName:", userName);
//    console.log("sellerName:", sellerName);
//    console.log("loginBtn:", loginButton);
//    console.log("registerBtn:", registerBtn);
//    console.log("logoutBtn:", logoutButton);


  if (userMenuBtn && userMenu) {
    userMenuBtn.addEventListener('click', (e) => {
      e.preventDefault();
      userMenu.classList.toggle('visible');
    });
  }

  const isLoggedIn = !!state.currentUser;
  const isSellerLoggedIn = !!state.currentSeller;

  if (userName) {
    if (state.currentUser) {
      userName.textContent = state.currentUser.full_name;
    } else if (!state.currentSeller) {
      userName.textContent = 'Account';
    } else {
      userName.textContent = ''; // clear if seller is logged in
    }
  }

  if (sellerName) {
    if (state.currentSeller) {
      sellerName.textContent = state.currentSeller.business_name;
    } else {
      sellerName.textContent = ''; // clear if buyer is logged in
    }
  }


  if (userDropdown) userDropdown.style.display = isLoggedIn || isSellerLoggedIn? 'block' : 'none';
  if (loginButton) loginButton.style.display = isLoggedIn || isSellerLoggedIn? 'none' : 'inline-block';
  if (registerBtn) registerBtn.style.display = isLoggedIn || isSellerLoggedIn? 'none' : 'inline-block';
  if (logoutButton) logoutButton.style.display = isLoggedIn || isSellerLoggedIn? 'inline-block' : 'none';
}


// =====BUYER=============//
// Replace the mock login function
window.register = async function register() {
    console.log("REGISTER FUNCTION CALLED");

    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;
    const phone = document.getElementById('registerPhone').value;

    if (!name || !email || !password || !confirmPassword) {
        showAlert('Please fill in all fields', 'error');
        return;
    }

    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'error');
        return;
    }

    try {
        const userData = {
            full_name: name,
            email: email,
            password: password,
            phone: SAUtils.formatPhone(phone)
        };

        const result = await api.register(userData);

         if (result.error) {
                showAlert(result.error, 'error');
                return;
            }
        if (result.user) {
        state.currentUser = result.user;
        localStorage.setItem('currentUser', JSON.stringify(result.user));
        } else {
         state.currentUser = result;
        }

//        updateAuthUI();
        showAlert(`Welcome ${state.currentUser.full_name}! 🎉`, 'success');
        console.log("localStorage currentUser:", localStorage.getItem('currentUser'));

//        localStorage.setItem('currentUser', JSON.stringify(state.currentUser));
        updateAuthUI();
        showPage('home');


    } catch (error) {
        handleApiError(error);
    }
}

// Replace the mock login function
window.login = async function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    if (!email || !password) {
        showAlert('Please enter email and password', 'error');
        return;
    }

     try {
            const result = await api.login({ email, password });

            state.currentUser = result.user || result;

            localStorage.setItem('currentUser', JSON.stringify(result.user));
            showAlert(`Welcome back ${result.user.full_name}! 👋`, 'success');
            console.log("localStorage currentUser:", localStorage.getItem('currentUser'));

//            localStorage.setItem('currentUser', JSON.stringify(result.user));
            updateAuthUI();
            showPage('home');
    } catch (error) {
        showAlert(error.message || 'Invalid email or password', 'error');
    }
};


// ============= SELLER =============//
// Replace the mock login function
window.seller_register = async function seller_register() {
    console.log("SELLER REGISTER FUNCTION CALLED");

    const business_name = document.getElementById('sellerRegisterName').value;
    const email = document.getElementById('sellerRegisterEmail').value;
    const password = document.getElementById('sellerRegisterPassword').value;
    const confirmPassword = document.getElementById('sellerRegisterConfirmPassword').value;
    const phone = document.getElementById('sellerRegisterPhone').value;

    if (!business_name || !email || !password || !confirmPassword || !phone) {
        showAlert('Please fill in all fields', 'error');
        return;
    }

    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'error');
        return;
    }

    try {
        const sellerData = {
            business_name: business_name,
            email: email,
            password: password,
            phone: SAUtils.formatPhone(phone)
        };

        const result = await api.seller_register(sellerData);

         if (result.error) {
                showAlert(result.error, 'error');
                return;
            }
        if (result.currentSeller) {
        state.currentSeller = result.user;
        localStorage.setItem('currentSeller', JSON.stringify(result.user));
        } else {
         state.currentSeller = result;
        }

        showAlert(`Welcome ${state.currentSeller.business_name}! 🎉`, 'success');
        console.log("localStorage currentSeller:", localStorage.getItem('currentSeller'));
        updateAuthUI();
//        localStorage.setItem('currentUser', JSON.stringify(state.currentUser));
        showPage('seller-dashboard');
        closeSellerModal();
//        document.getElementById('sellerRegisterModal').style.display = 'none';
//        updateAuthUI();
//        showPage('seller-dashboard');


    } catch (error) {
        handleApiError(error);
    }
}

// Replace the mock login function
window.seller_login = async function sellerLogin() {
    const email = document.getElementById('sellerLoginEmail').value;
    const password = document.getElementById('sellerLoginPassword').value;

    if (!email || !password) {
        showAlert('Please enter email and password', 'error');
        return;
    }

     try {
            const result = await api.seller_login({ email, password });

            state.currentSeller = result.currentSeller || result;

            localStorage.setItem('currentSeller', JSON.stringify(result.currentSeller));
            showAlert(`Welcome back ${result.currentSeller.business_name}! 👋`, 'success');
             updateAuthUI();
            console.log("localStorage currentSeller:", localStorage.getItem('currentSeller'));

//            localStorage.setItem('currentUser', JSON.stringify(result.user));

            showPage('seller-dashboard');
            closeSellerModal();
//            document.getElementById('sellerLoginModal').style.display = 'none';
//            updateAuthUI();
//            showPage('seller-dashboard');
    } catch (error) {
        showAlert(error.message || 'Invalid email or password', 'error');
    }
};
function logout() {
  // Clear state
  state.currentUser = null;
  state.currentSeller = null;

  // Clear storage
  localStorage.removeItem('currentUser');
  sessionStorage.removeItem('currentUser'); // if you used sessionStorage

  // Update UI
  updateAuthUI();

  // Optionally redirect
  showPage('home');
}


// Replace the mock product loading
async function loadFeaturedProducts() {
    const featuredContainer = document.getElementById('featuredProducts');
    featuredContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const result = await api.getProducts({ featured: true, limit: 6 });

        featuredContainer.innerHTML = '';

        if (result.products.length === 0) {
            featuredContainer.innerHTML = '<p class="text-center">No featured products available.</p>';
            return;
        }

        result.products.forEach(product => {
            const price = Number(product.price || 0);
            const formattedPrice = price.toFixed(2);

            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.innerHTML = `
                <div class="product-media">
                  <img src="${product.images && product.images[0] ? product.images[0] : '/static/uploads/images/no-image.png'}"
                                   alt="${product.name}">
                  </div>
                  <div class="product-info">
                      <div class="product-title">${product.name}</div>
                      <div class="product-price">R${formattedPrice}</div>
                      <div class="product-seller">Sold by: ${product.seller_name || 'Unknown Seller'}</div>
                 </div>
                 <div class="product-actions">
                      <button class="btn btn-primary" onclick="addToCart(${product.id})">
                          <i class="fas fa-cart-plus"></i> Add to Cart
                      </button>
                 </div>
                 `;
                 featuredContainer.appendChild(productCard)
               });
    } catch (error) {
        featuredContainer.innerHTML = '<p class="text-center">Error loading featured products.</p>';
        handleApiError(error);
    }
}
async function loadAllProducts() {
    const productsContainer = document.getElementById('allProducts');
    productsContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        // Get filter values
        const searchTerm = document.getElementById('searchInput').value;
        const categoryFilters = getSelectedCategories();
        const priceRange = document.querySelector('input[name="price"]:checked').value;
        const conditions = getSelectedConditions();

        const filters = {};

        if (searchTerm) filters.search = searchTerm;
        if (categoryFilters.length > 0) filters.categories = categoryFilters;
        if (priceRange !== 'all') filters.price_range = priceRange;
        if (conditions.length > 0) filters.conditions = conditions;

        const result = await api.getProducts(filters);

        productsContainer.innerHTML = '';

        if (result.products.length === 0) {
            productsContainer.innerHTML = '<p class="text-center">No products found matching your criteria.</p>';
            return;
        }

        result.products.forEach(product => {
        const price = Number(product.price || 0);
        const formattedPrice = price.toFixed(2);

        const productCard = document.createElement('div');
        productCard.className = 'product-card';
        productCard.innerHTML =
           ` <div class="product-media">
              <img src="${product.images && product.images[0] ? product.images[0] : '/static/uploads/images/no-image.png'}"
                               alt="${product.name}">
             </div>
             <div class="product-info">
                  <div class="product-title">${product.name}</div>
                  <div class="product-price">R${formattedPrice}</div>
                  <div class="product-seller">Sold by: ${product.seller_name || 'Unknown Seller'}</div>
                  </div>
                  <div class="product-actions">
                     <button class="btn btn-primary" onclick="addToCart(${product.id})">
                        <i class="fas fa-cart-plus"></i> Add to Cart
                     </button>
                  </div>
                  `;
           productsContainer.appendChild(productCard); });

    } catch (error) {
        productsContainer.innerHTML = '<p class="text-center">Error loading products.</p>';
        handleApiError(error);
    }
}

// Replace the mock addToCart function
async function addToCart(productId) {
    if (!state.currentUser) {
        showAlert('Please login to add items to your cart', 'error');
        showPage('login');
        return;
    }

    try {
        await api.addToCart(productId, 1);
        showAlert('Product added to cart!', 'success');
        await loadCart(); // Refresh cart
    } catch (error) {
        handleApiError(error);
    }
}
// Replace the mock loadCart function
async function loadCart() {
    if (!state.currentUser) {
        showAlert('Please login to view your cart', 'error');
        showPage('login');
        return;
    }

    const cartContainer = document.getElementById('cartItems');
    cartContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const result = await api.getCart();

        cartContainer.innerHTML = '';
        state.cart = result.cart_items || [];

        if (state.cart.length === 0) {
            cartContainer.innerHTML = `
                <div class="cart-empty">
                    <div class="cart-empty-icon">
                        <i class="fas fa-shopping-cart"></i>
                    </div>
                    <h3>Your cart is empty</h3>
                    <p>Add some products to your cart to see them here</p>
                    <button class="btn btn-primary" onclick="showPage('products')">Continue Shopping</button>
                </div>
            `;
            document.getElementById('cartTotal').textContent = '0.00';
            updateCartCount();
            return;
        }

        let total = 0;

        state.cart.forEach(item => {
        // Convert price to number safely
        const price = Number(item.product.price || 0);
        const itemTotal = price * item.quantity;
        total += itemTotal;

            const cartItem = document.createElement('div');
            cartItem.className = 'cart-item';
            cartItem.innerHTML = `
                <div class="cart-item-image">
                    <img src="${item.product.images && item.product.images[0] ? item.product.images[0] : 'static/uploads/images/no-image.png'}" alt="${item.product.name}">
                </div>
                <div class="cart-item-details">
                    <div class="cart-item-title">${item.product.name}</div>
                    <div class="cart-item-price">R${item.product.price.toFixed(2)}</div>
                    <div class="cart-item-seller">Sold by: ${item.product.seller_name || 'Unknown Seller'}</div>
                </div>
                <div class="cart-item-actions">
                    <div class="quantity-control">
                        <button class="quantity-btn" onclick="updateQuantity(${item.product.id}, ${item.quantity - 1})">
                            <i class="fas fa-minus"></i>
                        </button>
                        <input type="text" class="quantity-input" value="${item.quantity}" readonly>
                        <button class="quantity-btn" onclick="updateQuantity(${item.product.id}, ${item.quantity + 1})">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="removeFromCart(${item.product.id})">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                </div>
            `;
            cartContainer.appendChild(cartItem);
        });

        document.getElementById('cartTotal').textContent = total.toFixed(2);
        updateCartCount();
        updateCheckoutSummary();

    } catch (error) {
        cartContainer.innerHTML = '<p class="text-center">Error loading cart.</p>';
        handleApiError(error);
    }
}

// Replace the mock updateQuantity function
async function updateQuantity(productId, newQuantity) {
    if (newQuantity <= 0) {
        await removeFromCart(productId);
        return;
    }
    try {
        await api.updateCartItem(productId, newQuantity);
        await loadCart();

    } catch (error) {
        handleApiError(error);
    }
}

// Replace the mock removeFromCart function
async function removeFromCart(productId) {
    try {
        await api.removeFromCart(productId);
        await loadCart();
        showAlert('Item removed from cart', 'success');

    } catch (error) {
        handleApiError(error);
    }
}

// Replace the mock processPayment function
async function processPayment() {
    if (!state.currentUser) {
        showAlert('Please login to complete your purchase', 'error');
        showPage('login');
        return;
    }

    if (state.cart.length === 0) {
        showAlert('Your cart is empty', 'error');
        return;
    }

    // Collect shipping information
    const shippingInfo = {
        name: document.getElementById('shippingName').value,
        address: document.getElementById('shippingAddress').value,
        city: document.getElementById('shippingCity').value,
        province: document.getElementById('shippingProvince').value,
        postal_code: document.getElementById('shippingPostalCode').value,
        phone: document.getElementById('shippingPhone').value
    };

    const paymentMethod = document.querySelector('.payment-method.active').dataset.method;

    if (!shippingInfo.name || !shippingInfo.address || !shippingInfo.city) {
        showAlert('Please fill in all shipping information', 'error');
        return;
    }

    // Show payment processing modal
    document.getElementById('paymentModal').classList.remove('hidden');

    try {
        const orderData = {
            shipping_address: shippingInfo,
            payment_method: paymentMethod
        };

        const result = await api.createOrder(orderData);

        // Process payment
        const paymentData = {
            order_id: result.order_id,
            amount: result.total_amount,
            payment_method: paymentMethod
        };

        const paymentResult = await api.processPayment(paymentData);

        if (paymentResult.success) {
            document.getElementById('paymentStatus').innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    <div>
                        <h4>Payment Successful!</h4>
                        <p>Your order has been placed successfully.</p>
                        <p><strong>Order ID:</strong> ${result.order_number}</p>
                    </div>
                </div>
                <div class="text-center mt-20">
                    <button class="btn btn-primary" onclick="closePaymentModalAndRedirect()">View Order</button>
                </div>
            `;

            // Clear cart
            state.cart = [];
            updateCartCount();

        } else {
            throw new Error(paymentResult.message || 'Payment failed');
        }

    } catch (error) {
        document.getElementById('paymentStatus').innerHTML = `
            <div class="alert alert-error">
                <i class="fas fa-times-circle"></i>
                <div>
                    <h4>Payment Failed</h4>
                    <p>${error.message}</p>
                </div>
            </div>
            <div class="text-center mt-20">
                <button class="btn btn-primary" onclick="retryPayment()">Retry Payment</button>
                <button class="btn btn-outline" onclick="closePaymentModal()">Cancel</button>
            </div>
        `;
    }
}

// Replace the mock addProduct function for sellers
async function addProduct() {
    if (!state.currentSeller) {
        showAlert('Please login as a seller to add products', 'error');
        return;
    }

    const name = document.getElementById('productName').value;
    const description = document.getElementById('productDescription').value;
    const price = parseFloat(document.getElementById('productPrice').value);
    const originalPrice = parseFloat(document.getElementById('productOriginalPrice').value) || price;
    const categoryId = parseInt(document.getElementById('productCategory').value);
    const condition = document.getElementById('productCondition').value;
    const size = document.getElementById('productSize').value;
    const color = document.getElementById('productColor').value;
    const brand = document.getElementById('productBrand').value;
    const material = document.getElementById('productMaterial').value;
    const stock = parseInt(document.getElementById('productStock').value) || 1;

    if (!name || !description || !price || !categoryId) {
        showAlert('Please fill in all required fields', 'error');
        return;
    }

    if (state.mediaUploads.length === 0) {
        showAlert('Please add at least one image or video', 'error');
        return;
    }

    try {
        // First upload media files
        const mediaFiles = state.mediaUploads.map(upload => upload.file);
        const uploadResult = await api.uploadMedia(mediaFiles);

        // Then create product with media URLs
        const productData = {
            name: name,
            description: description,
            price: price,
            original_price: originalPrice,
            category_id: categoryId,
            condition: condition,
            size: size,
            color: color,
            brand: brand,
            material: material,
            stock_quantity: stock,
            images: uploadResult.images || [],
            videos: uploadResult.videos || []
        };

        await api.createProduct(productData);

        resetProductForm();
        showAlert('Product added successfully!', 'success');
        switchDashboardTab('products');
        loadSellerProducts();

    } catch (error) {
        handleApiError(error);
    }
}

// Replace the mock loadSellerProducts function
async function loadSellerProducts() {
    if (!state.currentSeller) {
        return;
    }

    const sellerProductsContainer = document.getElementById('sellerProducts');
    sellerProductsContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const result = await api.getSellerProducts();

        sellerProductsContainer.innerHTML = '';

        if (!result.products || result.products.length === 0) {
            sellerProductsContainer.innerHTML = '<p>No products yet. Add your first product!</p>';
            return;
        }

        result.products.forEach(product => {
            const imageSrc = (product.images && product.images[0])
                ? product.images[0]
                : '/static/uploads/images/no-image.png';  // ✅ correct fallback path

            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.innerHTML = `
                <div class="product-media">
                   <img src="${imageSrc}" alt="${product.name}" class="product-image">
                </div>
                <div class="product-info">
                    <div class="product-title">${product.name}</div>
                    <div class="product-price">R${(Number(product.price) || 0).toFixed(2)}</div>
                    <div class="product-actions">
                        <button class="btn btn-sm" onclick="editProduct(${product.id})">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteProduct(${product.id})">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `;
            sellerProductsContainer.appendChild(productCard);
        });

    } catch (error) {
        sellerProductsContainer.innerHTML = '<p>Error loading products.</p>';
        handleApiError(error);
    }
}


// Helper functions for filters
function getSelectedCategories() {
    const selected = [];
    state.categories.forEach(category => {
        const checkbox = document.getElementById(`category${category.id}`);
        if (checkbox && checkbox.checked) {
            selected.push(category.id);
        }
    });
    return selected;
}

function getSelectedConditions() {
    const selected = [];
    if (document.getElementById('conditionExcellent').checked) selected.push('excellent');
    if (document.getElementById('conditionGood').checked) selected.push('good');
    if (document.getElementById('conditionFair').checked) selected.push('fair');
    return selected;
}

// Update the initialization to load categories from backend
async function init() {
    try {
        // Load categories
        const categoriesResult = await api.getCategories();
        state.categories = categoriesResult.categories;
        loadCategories();

        // Check if user is logged in
//        if (api.isAuthenticated()) {
            try {
               const userResult = await api.getCurrentUser();
                if (userResult.user) {
                    state.currentUser = userResult.user;
                    localStorage.setItem('currentUser', JSON.stringify(userResult.user));
                } else if (userResult.seller) {
                    state.currentSeller = userResult.seller;
                    localStorage.setItem('currentSeller', JSON.stringify(userResult.seller));
                }
            } catch (error) {
                // Token might be invalid, clear it
                api.logout();
            }
//        }

        updateAuthUI();

        // Load initial data
        await loadFeaturedProducts();
        await loadAllProducts();

        // Load cart if user is logged in
        if (state.currentUser) {
            await loadCart();
        }

        // Show home page
        showPage('home');

    } catch (error) {
        console.error('Initialization error:', error);
        // Continue with mock data if backend is not available
        loadFeaturedProducts();
        loadAllProducts();
        showPage('home');
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BackendConnector, SAUtils, api, handleApiError };
}



