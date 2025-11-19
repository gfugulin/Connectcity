// Sistema simples de navegação entre páginas
const router = {
  /**
   * Navega para uma página
   * @param {string} page - Nome da página (sem .html)
   */
  navigate(page) {
    window.location.href = `${page}.html`;
  },

  /**
   * Inicializa navegação do footer
   */
  initFooterNavigation() {
    document.querySelectorAll('footer a[href="#"]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const text = link.textContent.trim().toLowerCase();
        
        const routes = {
          'rotas': 'index',
          'favoritos': 'favorites',
          'perfil': 'profile'
        };
        
        const page = routes[text] || 'index';
        this.navigate(page);
      });
    });
  },

  /**
   * Adiciona botão voltar funcional
   */
  initBackButton() {
    const backBtn = document.querySelector('header button, .arrow_back');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        window.history.back();
      });
    }
  }
};

// Inicializar ao carregar
window.addEventListener('DOMContentLoaded', () => {
  router.initFooterNavigation();
  router.initBackButton();
});

