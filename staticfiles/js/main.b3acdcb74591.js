/* Handles global UI interactions like sidebar and navigation */
class MasterLayoutManager {
  constructor() {
    this.selectors = {
      sidebarToggle: "#sidebarToggle",
      sidebar: "#sidebar",
      sidebarOverlay: "#sidebarOverlay",
      dropdownToggle: ".nav-dropdown-toggle",
      dropdownMenu: ".nav-dropdown-menu",
      chevronIcon: ".fa-chevron-down",
    };

    this.init();
  }

  /**
   * Initialize the layout manager
   */
  init() {
    this.setupSidebarToggle();
    this.setupDropdowns();
  }

  /**
   * Setup sidebar toggle functionality
   */
  setupSidebarToggle() {
    // Mobile sidebar toggle
    $(this.selectors.sidebarToggle).on("click", () => {
      this.toggleSidebar();
    });

    // Close sidebar when clicking overlay
    $(this.selectors.sidebarOverlay).on("click", () => {
      this.closeSidebar();
    });
  }

  /**
   * Toggle sidebar visibility
   */
  toggleSidebar() {
    $(this.selectors.sidebar).toggleClass("show");
    $(this.selectors.sidebarOverlay).toggleClass("show");
  }

  /**
   * Close sidebar
   */
  closeSidebar() {
    $(this.selectors.sidebar).removeClass("show");
    $(this.selectors.sidebarOverlay).removeClass("show");
  }

  /**
   * Setup dropdown functionality
   */
  setupDropdowns() {
    $(this.selectors.dropdownToggle).on("click", (e) => {
      e.preventDefault();
      this.toggleDropdown($(e.currentTarget));
    });
  }

  /**
   * Toggle dropdown menu
   */
  toggleDropdown($toggle) {
    const $menu = $toggle.next(this.selectors.dropdownMenu);
    const $chevron = $toggle.find(this.selectors.chevronIcon);

    $menu.toggleClass("show");
    $chevron.toggleClass("fa-chevron-up");
  }

  /**
   * Close all dropdowns (useful for mobile)
   */
  closeAllDropdowns() {
    $(this.selectors.dropdownMenu).removeClass("show");
    $(this.selectors.chevronIcon).removeClass("fa-chevron-up");
  }
}

// Initialize when DOM is ready
$(document).ready(function () {
  window.masterLayout = new MasterLayoutManager();
});
