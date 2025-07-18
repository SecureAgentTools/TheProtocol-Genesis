# AgentVault Registry UI Architecture

**Component**: Registry Frontend  
**Version**: 1.0.0  
**Last Updated**: Tuesday, June 17, 2025

---

## Overview

The AgentVault Registry UI is a single-page application (SPA) built with vanilla JavaScript and Bootstrap 5. It provides a comprehensive interface for agent management, discovery, and administration.

---

## Architecture

### Core Components

```
static/
├── js/
│   ├── app.js              # Main application controller
│   ├── router.js           # Client-side routing
│   ├── api.js              # API client
│   ├── auth.js             # Authentication management
│   ├── config.js           # Configuration
│   └── views/              # View modules
│       ├── login.js
│       ├── register.js
│       ├── dashboard.js
│       ├── mission_control.js
│       ├── developer.js
│       ├── discovery.js
│       ├── settings.js
│       └── ...
├── css/
│   ├── styles.css          # Main styles
│   └── dark-mode.css       # Dark theme
└── img/
    └── logo.svg            # Brand assets
```

### Key Design Principles

1. **No Framework Dependencies**: Pure JavaScript for maximum compatibility
2. **Modular Architecture**: Each view is a self-contained module
3. **Event-Driven**: Communication via custom events
4. **Progressive Enhancement**: Works without JavaScript for critical paths
5. **Responsive Design**: Mobile-first with Bootstrap grid

---

## Core Modules

### App.js - Application Controller

The main application entry point that orchestrates all components.

```javascript
class App {
    static async init() {
        // Initialize authentication
        await Auth.init();
        
        // Setup router
        Router.init();
        
        // Load initial view
        if (!Auth.isAuthenticated()) {
            window.location.href = '/ui/login';
        } else {
            Router.navigate(Auth.getDefaultView());
        }
    }
    
    static showOnboardingModal() {
        // Unified onboarding modal
        const modal = new OnboardingModal();
        modal.show();
    }
}
```

### Router.js - Client-Side Routing

Handles navigation without page reloads.

```javascript
class Router {
    static routes = {
        'dashboard': DashboardView,
        'mission-control': MissionControlView,
        'developer': DeveloperView,
        'discovery': DiscoveryView,
        'settings': SettingsView,
        'agent-details': AgentDetailsView
    };
    
    static navigate(route, params = {}) {
        // Update URL without reload
        history.pushState({route, params}, '', `/ui/${route}`);
        
        // Load view
        this.loadView(route, params);
    }
    
    static loadView(route, params) {
        const ViewClass = this.routes[route];
        if (ViewClass) {
            const view = new ViewClass(params);
            view.render();
        }
    }
}
```

### API.js - API Client

Centralized API communication with authentication handling.

```javascript
class API {
    static async request(endpoint, options = {}) {
        const token = Auth.getToken();
        
        const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : '',
                ...options.headers
            }
        });
        
        if (response.status === 401) {
            // Token expired, try refresh
            await Auth.refresh();
            return this.request(endpoint, options);
        }
        
        return response.json();
    }
    
    // Convenience methods
    static get(endpoint) {
        return this.request(endpoint);
    }
    
    static post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}
```

### Auth.js - Authentication Management

Handles login, logout, token management, and user state.

```javascript
class Auth {
    static TOKEN_KEY = 'agentvault_token';
    static USER_KEY = 'agentvault_user';
    
    static async login(email, password) {
        const response = await API.post('/auth/login', {email, password});
        
        if (response.access_token) {
            localStorage.setItem(this.TOKEN_KEY, response.access_token);
            localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
            
            // Redirect based on role
            if (response.user.role === 'admin') {
                Router.navigate('developer');
            } else {
                Router.navigate('dashboard');
            }
        }
        
        return response;
    }
    
    static logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        window.location.href = '/ui/login';
    }
    
    static isAuthenticated() {
        return !!this.getToken();
    }
    
    static isAdmin() {
        const user = this.getUser();
        return user && user.role === 'admin';
    }
}
```

---

## View Components

### Base View Class

All views extend this base class for consistent behavior.

```javascript
class BaseView {
    constructor(params = {}) {
        this.params = params;
        this.container = document.getElementById('app-content');
    }
    
    async render() {
        this.container.innerHTML = this.getLoadingHTML();
        
        try {
            const data = await this.fetchData();
            this.container.innerHTML = this.getHTML(data);
            this.attachEventListeners();
        } catch (error) {
            this.showError(error);
        }
    }
    
    // Override in subclasses
    async fetchData() {}
    getHTML(data) {}
    attachEventListeners() {}
}
```

### Dashboard View

Classic dashboard with statistics and quick actions.

```javascript
class DashboardView extends BaseView {
    async fetchData() {
        const [stats, recentAgents] = await Promise.all([
            API.get('/dashboard/stats'),
            API.get('/agents?limit=5')
        ]);
        
        return { stats, recentAgents };
    }
    
    getHTML(data) {
        return `
            <div class="dashboard">
                <h1>Agent Dashboard</h1>
                
                <!-- Statistics Cards -->
                <div class="row stats-row">
                    <div class="col-md-3">
                        <div class="stat-card">
                            <h3>${data.stats.total_agents}</h3>
                            <p>Total Agents</p>
                        </div>
                    </div>
                    <!-- More stats... -->
                </div>
                
                <!-- Quick Actions -->
                <div class="quick-actions">
                    <button class="btn btn-primary" onclick="App.showOnboardingModal()">
                        Onboard New Agent
                    </button>
                </div>
                
                <!-- Recent Agents -->
                <div class="recent-agents">
                    ${this.renderAgentList(data.recentAgents)}
                </div>
            </div>
        `;
    }
}
```

### Developer Portal View

Advanced interface for agent management.

```javascript
class DeveloperView extends BaseView {
    async fetchData() {
        const agents = await API.get('/agents?developer_id=me');
        return { agents };
    }
    
    getHTML(data) {
        return `
            <div class="developer-portal">
                <h1>Developer Portal</h1>
                
                <!-- Action Bar -->
                <div class="action-bar">
                    <button class="btn btn-primary" onclick="App.showOnboardingModal()">
                        Create Agent
                    </button>
                    <button class="btn btn-secondary" onclick="this.exportAgents()">
                        Export Data
                    </button>
                </div>
                
                <!-- Agents Table -->
                <table class="table agents-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.agents.map(agent => this.renderAgentRow(agent)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    renderAgentRow(agent) {
        return `
            <tr>
                <td>${agent.name}</td>
                <td><span class="badge bg-info">${agent.agent_type}</span></td>
                <td><span class="badge bg-success">${agent.status}</span></td>
                <td>${new Date(agent.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="Router.navigate('agent-details', {id: '${agent.id}'})">
                        Details
                    </button>
                    <button class="btn btn-sm btn-outline-danger"
                            onclick="DeveloperView.deleteAgent('${agent.id}')">
                        Delete
                    </button>
                </td>
            </tr>
        `;
    }
}
```

### Discovery/Galactic Map View

Visual agent browser with federation support.

```javascript
class DiscoveryView extends BaseView {
    constructor(params) {
        super(params);
        this.includeFederated = false;
    }
    
    async fetchData() {
        const endpoint = `/discovery/agents?include_federated=${this.includeFederated}`;
        return await API.get(endpoint);
    }
    
    getHTML(data) {
        return `
            <div class="discovery-view">
                <h1>Agent Discovery - Galactic Map</h1>
                
                <!-- Controls -->
                <div class="controls">
                    <input type="search" class="form-control" 
                           placeholder="Search agents..." 
                           onchange="this.search(event)">
                    
                    <div class="form-check">
                        <input type="checkbox" id="federated-check"
                               ${this.includeFederated ? 'checked' : ''}
                               onchange="this.toggleFederation(event)">
                        <label for="federated-check">
                            Include Federated Registries
                        </label>
                    </div>
                </div>
                
                <!-- Agent Grid -->
                <div class="agent-grid">
                    ${data.agents.map(agent => this.renderAgentCard(agent)).join('')}
                </div>
            </div>
        `;
    }
    
    renderAgentCard(agent) {
        return `
            <div class="agent-card ${agent.is_federated ? 'federated' : ''}">
                <div class="agent-header">
                    <h3>${agent.name}</h3>
                    <span class="agent-type">${agent.agent_type}</span>
                </div>
                <p class="agent-description">${agent.description}</p>
                <div class="agent-meta">
                    <small>by ${agent.developer_email}</small>
                    ${agent.is_federated ? `<small>via ${agent.registry_name}</small>` : ''}
                </div>
                <button class="btn btn-primary btn-sm"
                        onclick="DiscoveryView.showAgentDetails('${agent.id}')">
                    Details
                </button>
            </div>
        `;
    }
    
    static showAgentDetails(agentId) {
        // Show modal instead of navigation
        const modal = new AgentDetailsModal(agentId);
        modal.show();
    }
}
```

### Settings View

Comprehensive settings with four tabs.

```javascript
class SettingsView extends BaseView {
    constructor(params) {
        super(params);
        this.activeTab = params.tab || 'account';
    }
    
    getHTML(data) {
        return `
            <div class="settings-view">
                <h1>Settings</h1>
                
                <!-- Tab Navigation -->
                <ul class="nav nav-tabs">
                    <li class="nav-item">
                        <a class="nav-link ${this.activeTab === 'account' ? 'active' : ''}"
                           onclick="SettingsView.switchTab('account')">
                            Account
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link ${this.activeTab === 'api-keys' ? 'active' : ''}"
                           onclick="SettingsView.switchTab('api-keys')">
                            API Keys
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link ${this.activeTab === 'bootstrap' ? 'active' : ''}"
                           onclick="SettingsView.switchTab('bootstrap')">
                            Bootstrap Tokens
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link ${this.activeTab === 'preferences' ? 'active' : ''}"
                           onclick="SettingsView.switchTab('preferences')">
                            Preferences
                        </a>
                    </li>
                </ul>
                
                <!-- Tab Content -->
                <div class="tab-content">
                    ${this.getTabContent(this.activeTab, data)}
                </div>
            </div>
        `;
    }
}
```

---

## Modals and Components

### Onboarding Modal

Three-step agent creation wizard.

```javascript
class OnboardingModal {
    constructor() {
        this.currentStep = 1;
        this.bootstrapToken = null;
    }
    
    show() {
        const modalHTML = `
            <div class="modal fade" id="onboardingModal">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5>Onboard New Agent</h5>
                        </div>
                        <div class="modal-body">
                            ${this.getStepContent()}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal('#onboardingModal');
        modal.show();
    }
    
    getStepContent() {
        switch(this.currentStep) {
            case 1:
                return this.getTokenStepHTML();
            case 2:
                return this.getInstallStepHTML();
            case 3:
                return this.getRegisterStepHTML();
        }
    }
    
    async generateToken() {
        const response = await API.post('/onboard/bootstrap/request-token');
        this.bootstrapToken = response.token;
        this.updateTokenDisplay();
    }
}
```

---

## Styling and Themes

### Dark Mode Implementation

```css
/* dark-mode.css */
:root[data-theme="dark"] {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --border-color: #404040;
}

.dark-mode .card {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border-color: var(--border-color);
}

.dark-mode .agent-card {
    background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}
```

### Responsive Design

```css
/* Mobile First */
.agent-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
}

/* Tablet */
@media (min-width: 768px) {
    .agent-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop */
@media (min-width: 1200px) {
    .agent-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

---

## State Management

### Local Storage

```javascript
class Storage {
    static set(key, value) {
        localStorage.setItem(`agentvault_${key}`, JSON.stringify(value));
    }
    
    static get(key) {
        const value = localStorage.getItem(`agentvault_${key}`);
        return value ? JSON.parse(value) : null;
    }
    
    static remove(key) {
        localStorage.removeItem(`agentvault_${key}`);
    }
}
```

### Event System

```javascript
class EventBus {
    static events = {};
    
    static on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }
    
    static emit(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => callback(data));
        }
    }
}

// Usage
EventBus.on('agent:created', (agent) => {
    // Refresh agent list
    DashboardView.refreshAgents();
});
```

---

## Performance Optimizations

### Lazy Loading

```javascript
class LazyLoader {
    static async loadView(viewName) {
        if (!window[viewName]) {
            const module = await import(`./views/${viewName.toLowerCase()}.js`);
            window[viewName] = module.default;
        }
        return window[viewName];
    }
}
```

### Request Caching

```javascript
class APICache {
    static cache = new Map();
    static TTL = 5 * 60 * 1000; // 5 minutes
    
    static async get(endpoint) {
        const cached = this.cache.get(endpoint);
        
        if (cached && Date.now() - cached.timestamp < this.TTL) {
            return cached.data;
        }
        
        const data = await API.get(endpoint);
        this.cache.set(endpoint, {
            data,
            timestamp: Date.now()
        });
        
        return data;
    }
}
```

---

## Security Considerations

### XSS Prevention

```javascript
class SafeHTML {
    static escape(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    static sanitize(html) {
        // Use DOMPurify in production
        return DOMPurify.sanitize(html);
    }
}
```

### CSRF Protection

```javascript
class Security {
    static getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content;
    }
    
    static addCSRFHeader(headers) {
        const token = this.getCSRFToken();
        if (token) {
            headers['X-CSRF-Token'] = token;
        }
        return headers;
    }
}
```

---

## Testing

### Unit Tests

```javascript
// tests/auth.test.js
describe('Auth Module', () => {
    it('should store token on successful login', async () => {
        const mockResponse = {
            access_token: 'test-token',
            user: { id: '123', email: 'test@example.com' }
        };
        
        jest.spyOn(API, 'post').mockResolvedValue(mockResponse);
        
        await Auth.login('test@example.com', 'password');
        
        expect(localStorage.getItem('agentvault_token')).toBe('test-token');
    });
});
```

### Integration Tests

```javascript
// tests/e2e/login-flow.test.js
describe('Login Flow', () => {
    it('should redirect to dashboard after login', async () => {
        await page.goto('/ui/login');
        await page.fill('#email', 'test@example.com');
        await page.fill('#password', 'password');
        await page.click('#login-button');
        
        await page.waitForNavigation();
        expect(page.url()).toContain('/ui/dashboard');
    });
});
```

---

## Future Enhancements

1. **Progressive Web App (PWA)**: Offline support and installability
2. **WebSocket Integration**: Real-time updates for agent status
3. **Advanced Visualizations**: D3.js for complex data visualization
4. **Accessibility**: Full WCAG 2.1 AA compliance
5. **Internationalization**: Multi-language support

---

**End of UI Architecture Documentation**
