class SalesManager {
  constructor() {
    this.config = {
      csrfToken: this.getCSRFToken(),
      columnIndices: [0, 1, 2, 3, 4, 5],
      btnAddingCart: false,
      btnDeleteCart: false,
      cartClearing: false,
    };

    this.selectors = {
      table: "#sales_table",
      salesListUrl: "#sales_list_url",
      searchInput: "#products_search",
      clearFilter: "#filters_clear",
      cartCheckoutForm: "#cart_checkout_form",
      confirmSalesForm: "#confirm_sales_form",
      cartItemsBtn: "#cart_items_btn",
      clearCartBtn: "#clear_cart_btn",
      checkoutConfirmBtn: "#checkout_confirm_btn",
      checkoutCancelBtn: "#checkout_cancel_btn",
      checkCustomerNames: "#check_customerNames",
      checkComment: "#check_comment",
      confirmCheckoutModal: "#confirm_checkout_modal",
    };

    this.table = null;
    this.init();
  }

  /**
   * Get CSRF token from meta tag
   */
  getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute("content") : "";
  }

  /**
   * Initialize the application
   */
  init() {
    this.setupTable();
    this.setupEventHandlers();
  }

  /**
   * Generate alert messages
   */
  generateAlert(isSuccess, message) {
    const alertType = isSuccess ? "success" : "danger";
    const iconType = isSuccess ? "check" : "exclamation";

    return `
      <div class="alert alert-${alertType} alert-dismissible fade show px-2 m-0 d-block w-100">
        <i class='fas fa-${iconType}-circle'></i> ${message}
        <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button>
      </div>
    `;
  }

  /**
   * Setup DataTable
   */
  setupTable() {
    $(`${this.selectors.table} thead tr`)
      .clone(true)
      .attr("class", "filters")
      .appendTo(`${this.selectors.table} thead`);

    this.table = $(this.selectors.table).DataTable({
      fixedHeader: true,
      processing: true,
      serverSide: true,
      ajax: this.getAjaxConfig(),
      columns: this.getColumnConfig(),
      order: [[1, "asc"]],
      paging: true,
      lengthMenu: [
        [10, 20, 40, 50, 100, 200],
        [10, 20, 40, 50, 100, 200],
      ],
      pageLength: 10,
      lengthChange: true,
      autoWidth: true,
      searching: true,
      bInfo: true,
      bSort: true,
      orderCellsTop: true,
      columnDefs: this.getColumnDefs(),
      dom: "lBfrtip",
      buttons: [],
      initComplete: () => this.initTableFilters(),
    });
  }

  /**
   * Get AJAX configuration for DataTable
   */
  getAjaxConfig() {
    return {
      url: $(this.selectors.salesListUrl).val(),
      type: "POST",
      dataType: "json",
      headers: { "X-CSRFToken": this.config.csrfToken },
    };
  }

  /**
   * Get column configuration
   */
  getColumnConfig() {
    return [
      { data: "count" },
      { data: "name" },
      { data: "qty" },
      { data: "price" },
      { data: "sell_qty" },
      { data: "action" },
    ];
  }

  /**
   * Get column definitions
   */
  getColumnDefs() {
    return [
      {
        targets: [0, 4, 5],
        orderable: false,
      },
      {
        targets: 1,
        className: "ellipsis text-start",
        createdCell: (cell, cellData, rowData) => {
          const cellContent = `
            <a href="#" class="product-link">
              <div class="product-info">
                <div class="product-avatar">
                  <i class="fas fa-box-open"></i>
                </div>
                <span>${rowData.name}</span>
              </div>
            </a>`;
          $(cell).html(cellContent);
        },
      },
      {
        targets: [2, 3],
        className: "text-end pe-4",
      },
      {
        targets: 4,
        createdCell: (cell, cellData, rowData) => {
          const cart = rowData.cart > 0 ? rowData.cart : "";
          const cellContent = `
            <input type="number" min="1" step="0.1" class="form-control" 
                   id="qty_${rowData.id}" max="${rowData.sell_qty}" 
                   value="${cart}" placeholder="Enter quantity.."/>`;
          $(cell).html(cellContent);
        },
      },
      {
        targets: 5,
        className: "align-middle text-nowrap text-center",
        createdCell: (cell, cellData, rowData) => {
          const cellContent = `
            <button class="btn btn-success btn-sm" id="btn_${rowData.id}">
              <i class="fas fa-cart-plus"></i> Add
            </button>`;
          $(cell).html(cellContent);
        },
      },
    ];
  }

  /**
   * Initialize table filters
   */
  initTableFilters() {
    const api = this.table;

    api
      .columns(this.config.columnIndices)
      .eq(0)
      .each((colIdx) => {
        const cell = $(".filters th").eq(
          $(api.column(colIdx).header()).index()
        );
        cell.addClass("bg-white");

        if (colIdx === 0 || colIdx === 4 || colIdx === 5) {
          cell.html("");
        } else {
          const floatClass = colIdx === 1 ? "float-start" : "float-end";
          cell.html(`
            <input type="text" class="text-color6 ${floatClass}" placeholder="Filter.."/>
          `);
          this.setupColumnFilter(cell, api, colIdx);
        }
      });
  }

  /**
   * Setup individual column filter
   */
  setupColumnFilter(cell, api, colIdx) {
    const input = $("input", cell);

    input.off("keyup change").on("keyup change", function (e) {
      e.stopPropagation();
      $(this).attr("title", $(this).val());

      const regexr = "{search}";
      const cursorPosition = this.selectionStart;

      api
        .column(colIdx)
        .search(
          this.value !== "" ? regexr.replace("{search}", this.value) : "",
          this.value !== "",
          this.value === ""
        )
        .draw();

      $(this).focus()[0].setSelectionRange(cursorPosition, cursorPosition);
    });
  }

  /**
   * Setup all event handlers
   */
  setupEventHandlers() {
    this.setupSearchHandler();
    this.setupFilterHandler();
    this.setupClickHandlers();
  }

  /**
   * Setup search handler
   */
  setupSearchHandler() {
    $(this.selectors.searchInput)
      .off("keyup")
      .on("keyup", () => {
        this.table.search($(this.selectors.searchInput).val()).draw();
      });
  }

  /**
   * Setup filter handler
   */
  setupFilterHandler() {
    $(this.selectors.clearFilter)
      .off("click")
      .on("click", (e) => {
        e.preventDefault();
        $(this.selectors.searchInput).val("");
        this.table.search("").draw();
      });
  }

  /**
   * Setup click event handlers
   */
  setupClickHandlers() {
    document.addEventListener("click", (e) => {
      const clicked = $(e.target);

      if (
        clicked.is("#sales_table tr td button") ||
        clicked.is("#sales_table tr td button i")
      ) {
        this.handleAddToCart(clicked);
      } else if (
        clicked.is("#cart_checkout_form div span.del") ||
        clicked.is("#cart_checkout_form div span.del i")
      ) {
        this.handleDeleteCartItem(clicked);
      } else if (clicked.is(this.selectors.clearCartBtn)) {
        this.handleClearCart(clicked);
      } else if (clicked.is(this.selectors.checkoutConfirmBtn)) {
        this.handleCheckoutConfirm();
      }
    });
  }

  /**
   * Handle add to cart
   */
  handleAddToCart(clicked) {
    if (this.config.btnAddingCart) return;

    const btn = clicked.is("#sales_table tr td button")
      ? clicked
      : clicked.parent();
    const rowId = btn.attr("id").split("_")[1];
    const maxQty = parseFloat($(`#qty_${rowId}`).attr("max"));
    const valQty = parseFloat($(`#qty_${rowId}`).val());

    if (valQty > 0) {
      if (valQty <= maxQty) {
        $(`#qty_${rowId}`).css({
          border: "2px solid rgba(24, 132, 119, .6)",
          color: "#2D2D2D",
        });

        const formData = new FormData();
        formData.append("cart_add", "add_to_cart");
        formData.append("product", rowId);
        formData.append("qty", valQty);

        this.performAjaxRequest({
          url: $(this.selectors.cartCheckoutForm).attr("action"),
          data: formData,
          beforeSend: () => {
            this.config.btnAddingCart = true;
            btn.html(`<i class='fas fa-spinner fa-pulse'></i>`);
          },
          success: (response) => {
            this.config.btnAddingCart = false;
            btn.html(`<i class="fas fa-cart-plus"></i> Add`);
            if (response.success) {
              $(this.selectors.cartItemsBtn).text(response.cart);
              $(this.selectors.cartCheckoutForm).load(
                `${location.href} ${this.selectors.cartCheckoutForm}`
              );
              $(this.selectors.confirmSalesForm).load(
                `${location.href} ${this.selectors.confirmSalesForm}`
              );
            } else {
              window.alert("Unknown error occurred, reload & try again.");
            }
          },
          error: () => {
            this.config.btnAddingCart = false;
            btn.html(`<i class="fas fa-cart-plus"></i> Add`);
            window.alert("Unknown error occurred, reload & try again.");
          },
        });
      } else {
        $(`#qty_${rowId}`).css({
          border: "1px solid #FF4444",
          color: "#FF4444",
        });
      }
    }
  }

  /**
   * Handle delete cart item
   */
  handleDeleteCartItem(clicked) {
    if (this.config.btnDeleteCart) return;

    const btn = clicked.is("#cart_checkout_form div span.del")
      ? clicked
      : clicked.parent();
    const cartId = btn.attr("id").split("_")[1];
    const formData = new FormData();
    formData.append("cart_delete", parseInt(cartId));

    this.performAjaxRequest({
      url: $(this.selectors.cartCheckoutForm).attr("action"),
      data: formData,
      beforeSend: () => {
        this.config.btnDeleteCart = true;
        btn.html(`<i class='fas fa-spinner fa-pulse'></i>`);
      },
      success: (response) => {
        this.config.btnDeleteCart = false;
        if (response.success) {
          $(`#div_cart_${cartId}`).slideUp("fast");
          $(this.selectors.cartItemsBtn).text(response.cart);
          $("#grand_total_spn").text(response.grand_total);
          $(this.selectors.confirmSalesForm).load(
            `${location.href} ${this.selectors.confirmSalesForm}`
          );
          if (response.cart == 0) {
            $(this.selectors.cartCheckoutForm).load(
              `${location.href} ${this.selectors.cartCheckoutForm}`
            );
          }
          this.table.draw();
        } else {
          btn.html(`<i class="fas fa-trash-alt"></i>`);
          window.alert(response.sms);
        }
      },
      error: () => {
        this.config.btnDeleteCart = false;
        btn.html(`<i class="fas fa-trash-alt"></i>`);
        window.alert("Failed to delete item, reload & try again");
      },
    });
  }

  /**
   * Handle clear cart
   */
  handleClearCart(clicked) {
    if (this.config.cartClearing) return;

    const formData = new FormData();
    formData.append("clear_cart", "clear_cart");

    this.performAjaxRequest({
      url: $(this.selectors.cartCheckoutForm).attr("action"),
      data: formData,
      beforeSend: () => {
        this.config.cartClearing = true;
        clicked.html(`<i class='fas fa-spinner fa-pulse'></i>`);
      },
      success: (response) => {
        this.config.cartClearing = false;
        if (response.success) {
          $(this.selectors.cartItemsBtn).text("0");
          this.table.draw();
          $(this.selectors.cartCheckoutForm).load(
            `${location.href} ${this.selectors.cartCheckoutForm}`
          );
        } else {
          clicked.html(`Clear`);
          window.alert(response.sms);
        }
      },
      error: () => {
        this.config.cartClearing = false;
        clicked.html(`Clear`);
        window.alert("Failed to clear items, reload & try again");
      },
    });
  }

  /**
   * Handle checkout confirmation
   */
  handleCheckoutConfirm() {
    const formData = new FormData();
    formData.append("checkout", "checkout");
    formData.append("customer", $(this.selectors.checkCustomerNames).val());
    formData.append("comment", $(this.selectors.checkComment).val());

    this.performAjaxRequest({
      url: $(this.selectors.cartCheckoutForm).attr("action"),
      data: formData,
      beforeSend: () => {
        $(this.selectors.checkoutCancelBtn)
          .removeClass("d-inline-block")
          .addClass("d-none");
        $(this.selectors.checkoutConfirmBtn)
          .html("<i class='fas fa-spinner fa-pulse'></i>")
          .attr("type", "button");
      },
      success: (response) => {
        $(this.selectors.checkoutCancelBtn)
          .removeClass("d-none")
          .addClass("d-inline-block");
        $(this.selectors.checkoutConfirmBtn)
          .text("Continue")
          .attr("type", "submit");

        if (response.success) {
          $(this.selectors.cartItemsBtn).text("0");
          this.table.draw();
          $(this.selectors.cartCheckoutForm).load(
            `${location.href} ${this.selectors.cartCheckoutForm}`
          );
          $(this.selectors.checkoutConfirmBtn)
            .removeClass("d-inline-block")
            .addClass("d-none");
          $(`${this.selectors.confirmSalesForm} .form-floating`)
            .removeClass("text-color5")
            .addClass("text-color2");
          $(`${this.selectors.confirmSalesForm} .form-floating`).html(
            `<i class="fas fa-check-circle"></i> &nbsp; ${response.sms}`
          );
        } else {
          $(`${this.selectors.confirmSalesForm} .formsms`).html(
            this.generateAlert(response.success, response.sms)
          );
        }
      },
      error: () => {
        $(this.selectors.checkoutCancelBtn)
          .removeClass("d-none")
          .addClass("d-inline-block");
        $(this.selectors.checkoutConfirmBtn)
          .text("Save")
          .attr("type", "submit");
        $(`${this.selectors.confirmSalesForm} .formsms`).html(
          this.generateAlert(false, "Failed to checkout, reload & try again")
        );
      },
    });
  }

  /**
   * Perform AJAX request
   */
  performAjaxRequest({ url, data, beforeSend, success, error }) {
    $.ajax({
      type: "POST",
      url,
      data,
      dataType: "json",
      contentType: false,
      processData: false,
      headers: { "X-CSRFToken": this.config.csrfToken },
      beforeSend,
      success,
      error,
    });
  }
}

// Initialize the application when DOM is ready
$(function () {
  new SalesManager();
});
