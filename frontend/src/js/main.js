document.addEventListener('DOMContentLoaded', () => {
	const apiBaseUrl = 'http://127.0.0.1:8000';

	// Check if user is already logged in and redirect to dashboard
	const currentUser = localStorage.getItem('pim_username');
	if (currentUser && window.location.pathname.includes('index.html')) {
		window.location.href = 'dashboard.html';
		return;
	}

	// If on dashboard but no user, redirect to login
	if (window.location.pathname.includes('dashboard.html') && !currentUser) {
		window.location.href = 'index.html';
		return;
	}

	// Initialize based on current page
	if (window.location.pathname.includes('dashboard.html')) {
		initDashboard();
	} else {
		initLogin();
	}

	function initLogin() {
		const form = document.querySelector('form');
		const usernameInput = document.getElementById('username');
		const passwordInput = document.getElementById('password');
		const registerButton = document.querySelector('button.register');

		console.log('Login form elements:', {
			form,
			usernameInput,
			passwordInput,
			registerButton,
		});

		async function postJson(url, body) {
			try {
				console.log('Making API call to:', url);
				console.log('Request body:', body);

				const response = await fetch(url, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify(body),
				});

				console.log('Response status:', response.status);
				console.log('Response headers:', [...response.headers.entries()]);

				const data = await response.json().catch(() => ({}));
				console.log('Response data:', data);

				return { ok: response.ok, status: response.status, data };
			} catch (error) {
				console.error('API call failed:', error);
				return {
					ok: false,
					status: 0,
					data: { error: 'Network error: ' + error.message },
				};
			}
		}

		if (form) {
			form.addEventListener('submit', async (e) => {
				e.preventDefault();
				console.log('Form submitted');

				const username = usernameInput?.value?.trim();
				const password = passwordInput?.value ?? '';

				console.log('Login attempt:', {
					username,
					password: password ? '***' : 'empty',
				});

				if (!username || !password) {
					alert('Please enter both username and password.');
					return;
				}

				try {
					const { ok, status, data } = await postJson(
						`${apiBaseUrl}/auth/login`,
						{
							username,
							password,
						}
					);

					console.log('Login response:', { ok, status, data });

					if (ok) {
						localStorage.setItem('pim_username', username);
						window.location.href = 'dashboard.html';
					} else {
						alert(data?.error || `Login failed (status ${status})`);
					}
				} catch (error) {
					console.error('Login error:', error);
					alert(
						'Login failed due to a network error. Please check if the backend is running.'
					);
				}
			});
		} else {
			console.error('Login form not found!');
		}

		if (registerButton) {
			registerButton.addEventListener('click', async () => {
				const username = usernameInput?.value?.trim();
				const password = passwordInput?.value ?? '';
				if (!username || !password) {
					alert('Please enter both username and password to register.');
					return;
				}

				const { ok, status, data } = await postJson(
					`${apiBaseUrl}/auth/register`,
					{
						username,
						password,
					}
				);

				if (ok) {
					alert('Registration successful. You can now sign in.');
				} else {
					alert(data?.error || `Registration failed (status ${status})`);
				}
			});
		}
	}

	function initDashboard() {
		const currentUser = localStorage.getItem('pim_username');
		document.getElementById(
			'welcome-user'
		).textContent = `Welcome, ${currentUser}`;

		// Show loading screen initially
		const loadingScreen = document.getElementById('loading-screen');
		const mainContent = document.getElementById('main-content');

		// Initialize dashboard functionality
		initParticleManagement();
		initLogout();

		// Load articles and hide loading screen when done
		loadArticles().then(() => {
			// Add a small delay to show the loading animation
			setTimeout(() => {
				loadingScreen.style.opacity = '0';
				loadingScreen.style.transition = 'opacity 0.5s ease-out';

				setTimeout(() => {
					loadingScreen.style.display = 'none';
					mainContent.style.display = 'block';
				}, 500);
			}, 1500); // Show loading for at least 1.5 seconds
		});
	}

	function initLogout() {
		document.getElementById('logout-btn').addEventListener('click', () => {
			localStorage.removeItem('pim_username');
			window.location.href = 'index.html';
		});
	}

	function initParticleManagement() {
		const searchInput = document.getElementById('search-input');
		const searchBtn = document.getElementById('search-btn');
		const clearSearchBtn = document.getElementById('clear-search-btn');
		const createBtn = document.getElementById('create-particle-btn');
		const modal = document.getElementById('article-modal');
		const closeModal = document.getElementById('close-modal');
		const cancelArticle = document.getElementById('cancel-article');
		const articleForm = document.getElementById('article-form');
		const modalTitle = document.getElementById('modal-title');

		let currentEditingId = null;

		// Search functionality
		searchBtn.addEventListener('click', () => {
			const searchTerm = searchInput.value.trim();
			if (searchTerm) {
				searchArticles(searchTerm);
			} else {
				loadArticles();
			}
		});

		searchInput.addEventListener('keypress', (e) => {
			if (e.key === 'Enter') {
				searchBtn.click();
			}
		});

		clearSearchBtn.addEventListener('click', () => {
			searchInput.value = '';
			loadArticles();
		});

		// Create/Edit modal
		createBtn.addEventListener('click', () => {
			currentEditingId = null;
			modalTitle.textContent = 'Create New Article';
			articleForm.reset();
			modal.style.display = 'block';
		});

		closeModal.addEventListener('click', () => {
			modal.style.display = 'none';
		});

		cancelArticle.addEventListener('click', () => {
			modal.style.display = 'none';
		});

		// Close modal when clicking outside
		window.addEventListener('click', (e) => {
			if (e.target === modal) {
				modal.style.display = 'none';
			}
		});

		// Form submission
		articleForm.addEventListener('submit', async (e) => {
			e.preventDefault();
			const title = document.getElementById('article-title').value.trim();
			const content = document.getElementById('article-content').value.trim();

			if (!title || !content) {
				alert('Please fill in both title and content.');
				return;
			}

			if (currentEditingId) {
				await editArticle(currentEditingId, title, content);
			} else {
				await createArticle(title, content);
			}

			modal.style.display = 'none';
			loadArticles();
		});

		// Global functions for article operations
		window.editArticleClick = (articleId) => {
			currentEditingId = articleId;
			modalTitle.textContent = 'Edit Article';

			// Find the article data and populate the form
			const articleCard = document.querySelector(
				`[data-article-id="${articleId}"]`
			);
			const title = articleCard.querySelector('.article-title').textContent;
			const content = articleCard.querySelector('.article-content').textContent;

			document.getElementById('article-title').value = title;
			document.getElementById('article-content').value = content;
			modal.style.display = 'block';
		};

		window.viewArticleClick = (articleId) => {
    		const articleCard = document.querySelector(`[data-article-id="${articleId}"]`);
    		const title = articleCard.querySelector('.article-title').textContent;
    		const content = articleCard.querySelector('.article-content').textContent;
    		alert(`Title: ${title}\n\nContent:\n${content}`);
		};


		window.deleteArticleClick = async (articleId) => {
			if (confirm('Are you sure you want to delete this article?')) {
				await deleteArticle(articleId);
				loadArticles();
			}
		};
	}

	async function loadArticles() {
		const currentUser = localStorage.getItem('pim_username');
		try {
			const response = await fetch(`${apiBaseUrl}/particles/${currentUser}`);
			const data = await response.json();

			displayArticles(data.items || []);
		} catch (error) {
			console.error('Error loading articles:', error);
			displayArticles([]);
		}
	}

	async function searchArticles(searchTerm) {
		const currentUser = localStorage.getItem('pim_username');
		try {
			const response = await fetch(
				`${apiBaseUrl}/particles/${currentUser}/search?q=${encodeURIComponent(
					searchTerm
				)}`
			);
			const data = await response.json();

			displayArticles(data.items || []);
		} catch (error) {
			console.error('Error searching articles:', error);
			displayArticles([]);
		}
	}

	function displayArticles(articles) {
		const container = document.getElementById('articles-container');
		const noArticles = document.getElementById('no-articles');

		if (articles.length === 0) {
			container.innerHTML = '';
			noArticles.style.display = 'block';
			return;
		}

		noArticles.style.display = 'none';
		container.innerHTML = articles
			.map(
				(article) => `
			<div class="article-card" data-article-id="${
				article.particle_id || article.article_id
			}">
				<div class="article-header">
					<h3 class="article-title">${escapeHtml(article.title)}</h3>
					<div class="article-actions">
						<button class="article-btn edit-btn" onclick="editArticleClick('${
							article.particle_id || article.article_id
						}')">Edit</button>
						<button class="article-btn view-btn" onclick = "viewArticleClick('${
							article.particle_id || article.article_id
						}')">View</button>
						<button class="article-btn delete-btn" onclick="deleteArticleClick('${
							article.particle_id || article.article_id
						}')">Delete</button>
					</div>
				</div>
				<div class="article-content">${escapeHtml(article.content)}</div>
				<div class="article-meta">
					<span>ID: ${article.particle_id || article.article_id}</span>
				</div>
			</div>
		`
			)
			.join('');
	}

	async function createArticle(title, content) {
		const currentUser = localStorage.getItem('pim_username');
		const password = prompt('Enter your password to create this article:');

		if (!password) return;

		try {
			const response = await fetch(`${apiBaseUrl}/particles/create`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					username: currentUser,
					password: password,
					title: title,
					content: content,
				}),
			});

			const data = await response.json();

			if (response.ok) {
				alert('Article created successfully!');
			} else {
				alert(data.error || 'Failed to create article');
			}
		} catch (error) {
			console.error('Error creating article:', error);
			alert('Error creating article');
		}
	}

	async function editArticle(articleId, title, content) {
		const currentUser = localStorage.getItem('pim_username');
		const password = prompt('Enter your password to edit this article:');

		if (!password) return;

		try {
			const response = await fetch(`${apiBaseUrl}/particles/${articleId}`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					username: currentUser,
					password: password,
					title: title,
					content: content,
				}),
			});

			const data = await response.json();

			if (response.ok) {
				alert('Article updated successfully!');
			} else {
				alert(data.error || 'Failed to update article');
			}
		} catch (error) {
			console.error('Error updating article:', error);
			alert('Error updating article');
		}
	}

	async function deleteArticle(articleId) {
		try {
			const response = await fetch(`${apiBaseUrl}/particles/${articleId}`, {
				method: 'DELETE',
			});

			const data = await response.json();

			if (response.ok) {
				alert('Article deleted successfully!');
			} else {
				alert(data.error || 'Failed to delete article');
			}
		} catch (error) {
			console.error('Error deleting article:', error);
			alert('Error deleting article');
		}
	}

	function escapeHtml(text) {
		const div = document.createElement('div');
		div.textContent = text;
		return div.innerHTML;
	}
});
