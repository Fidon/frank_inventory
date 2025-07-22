class SalesReportManager {
  constructor() {
    this.config = {
      columnIndices: [0, 1, 2, 3, 4, 5, 6, 7],
      dateCache: { start: null, end: null },
      csrfToken: this.getCSRFToken(),
    };

    this.selectors = {
      table: "#reports_table",
      salesReportUrl: "#sales_report_url",
      shopsList: "#shops_list",
      searchInput: "#sales_search",
      clearFilter: "#sales_filter_clear",
      minDate: "#min_date",
      maxDate: "#max_date",
      dateClear: "#date_clear",
      dateFilterBtn: "#date_filter_btn",
      salesToggle: "#sales_toggle",
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
    $(this.selectors.salesToggle).click();
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
   * Format row for child details
   */
  formatRow(data) {
    let rowContents = "";
    data.items.forEach((item) => {
      rowContents += `
        <div class="d-block w-100 float-start text-start my-1 px-2">
          <span class="d-inline-block px-1">${item.count}.</span>
          <span class="d-inline-block px-1 mx-1">${item.names}</span>
          <span class="d-inline-block px-1 mx-1">${item.price} (${item.qty})</span>
          <span class="d-inline-block px-1">= &nbsp; ${item.total}</span>
        </div>`;
    });
    return rowContents;
  }

  /**
   * Format currency for display
   */
  formatCurrency(num) {
    return (
      num.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) + " TZS"
    );
  }

  /**
   * Date range management
   */
  getDateRange() {
    const minDateStr = $(this.selectors.minDate).val();
    const maxDateStr = $(this.selectors.maxDate).val();

    try {
      let dtStartUtc = null;
      let dtEndUtc = null;

      if (minDateStr) {
        const startDateLocal = new Date(`${minDateStr}T00:00:00.000`);
        if (isNaN(startDateLocal.getTime())) {
          throw new Error("Invalid start date format");
        }
        dtStartUtc = startDateLocal.toISOString();
      }

      if (maxDateStr) {
        const endDateLocal = new Date(`${maxDateStr}T23:59:59.999`);
        if (isNaN(endDateLocal.getTime())) {
          throw new Error("Invalid end date format");
        }
        dtEndUtc = endDateLocal.toISOString();
      }

      this.config.dateCache.start = dtStartUtc;
      this.config.dateCache.end = dtEndUtc;

      return { start: dtStartUtc, end: dtEndUtc };
    } catch (error) {
      console.error("Date processing error:", error);
      return { start: null, end: null };
    }
  }

  /**
   * Clear date filters
   */
  clearDates() {
    $(this.selectors.minDate).val("");
    $(this.selectors.maxDate).val("");
    this.config.dateCache.start = null;
    this.config.dateCache.end = null;
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
      order: [[2, "desc"]],
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
      dom: "lBfrtip",
      columnDefs: this.getColumnDefs(),
      buttons: this.getButtonConfig(),
      footerCallback: this.getFooterCallback(),
      initComplete: () => this.initTableFilters(),
      language: {
        lengthMenu: "Show _MENU_ rows",
        info: "Showing _START_ to _END_ of _TOTAL_ rows",
        infoEmpty: "Showing 0 to 0 of 0 rows",
        infoFiltered: "(filtered from _MAX_ total rows)",
        search: "Search:",
        paginate: {
          first: "First",
          last: "Last",
          next: "Next",
          previous: "Prev",
        },
      },
    });

    this.setupRowExpansion();
  }

  /**
   * Get AJAX configuration for DataTable
   */
  getAjaxConfig() {
    return {
      url: $(this.selectors.salesReportUrl).val(),
      type: "POST",
      data: (d) => {
        const dateRange = this.getDateRange();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": this.config.csrfToken },
      dataSrc: (json) => {
        $(`${this.selectors.table} tfoot tr:eq(1) th:eq(4)`)
          .html(json.grand_total)
          .addClass("text-end pe-3");
        $(`${this.selectors.table} tfoot tr:eq(1) th:eq(5)`)
          .html(json.grand_profit)
          .addClass("text-end pe-3");
        return json.data;
      },
    };
  }

  /**
   * Get column configuration
   */
  getColumnConfig() {
    return [
      {
        className: "dt-control text-success",
        data: null,
        defaultContent: `<i class='fas fa-circle-chevron-right'></i>`,
      },
      { data: "count" },
      { data: "saledate" },
      { data: "shop" },
      { data: "amount" },
      { data: "profit" },
      { data: "customer" },
      { data: "user" },
    ];
  }

  /**
   * Get column definitions
   */
  getColumnDefs() {
    return [
      {
        targets: [0, 1],
        orderable: false,
      },
      {
        targets: 2,
        createdCell: (cell) => $(cell).addClass("text-nowrap"),
      },
      {
        targets: [4, 5],
        createdCell: (cell) => $(cell).addClass("text-end pe-4"),
      },
      {
        targets: [6, 7],
        createdCell: (cell) => $(cell).addClass("ellipsis text-start ps-1"),
      },
    ];
  }

  /**
   * Get button configuration for DataTable
   */
  getButtonConfig() {
    const baseConfig = {
      className: "btn btn-extra text-white",
      title: "Sales report - FrankApp",
      exportOptions: { columns: [1, 2, 3, 4, 5, 6, 7] },
    };

    return [
      {
        extend: "copy",
        text: "<i class='fas fa-clone'></i>",
        titleAttr: "Copy",
        ...baseConfig,
      },
      {
        extend: "pdf",
        text: "<i class='fas fa-file-pdf'></i>",
        titleAttr: "Export to PDF",
        filename: "sales-report",
        orientation: "landscape",
        pageSize: "A4",
        footer: true,
        exportOptions: {
          ...baseConfig.exportOptions,
          search: "applied",
          order: "applied",
        },
        tableHeader: { alignment: "center" },
        customize: this.customizePDF.bind(this),
        ...baseConfig,
      },
      {
        extend: "excel",
        text: "<i class='fas fa-file-excel'></i>",
        titleAttr: "Export to Excel",
        ...baseConfig,
      },
      {
        extend: "print",
        text: "<i class='fas fa-print'></i>",
        titleAttr: "Print",
        orientation: "landscape",
        pageSize: "A4",
        footer: true,
        exportOptions: {
          ...baseConfig.exportOptions,
          search: "applied",
          order: "applied",
        },
        tableHeader: { alignment: "center" },
        customize: this.customizePrint.bind(this),
        ...baseConfig,
      },
    ];
  }

  /**
   * Customize PDF export
   */
  customizePDF(doc) {
    doc.styles.tableHeader.alignment = "center";
    doc.styles.tableBodyOdd.alignment = "center";
    doc.styles.tableBodyEven.alignment = "center";
    doc.styles.tableHeader.fontSize = 11;
    doc.defaultStyle.fontSize = 11;
    doc.content[1].table.widths = Array(doc.content[1].table.body[1].length + 1)
      .join("*")
      .split("");

    const body = doc.content[1].table.body;
    for (let i = 1; i < body.length; i++) {
      const cellConfigs = [
        { alignment: "center", margin: [3, 0, 0, 0] },
        { alignment: "center" },
        { alignment: "center" },
        { alignment: "right", padding: [0, 10, 0, 0] },
        { alignment: "right", padding: [0, 10, 0, 0] },
        { alignment: "left" },
        { alignment: "left", margin: [0, 0, 3, 0] },
      ];

      cellConfigs.forEach((config, j) => {
        if (body[i][j]) {
          Object.assign(body[i][j], config);
          body[i][j].style = "vertical-align: middle;";
        }
      });
    }
  }

  /**
   * Customize print output
   */
  customizePrint(win) {
    $(win.document.body).css("font-size", "11pt");
    $(win.document.body)
      .find("table")
      .addClass("compact")
      .css("font-size", "inherit");
  }

  /**
   * Get footer callback for DataTable
   */
  getFooterCallback() {
    return (row, data, start, end, display) => {
      const api = this.table;
      const intVal = (i) =>
        typeof i === "string"
          ? i.replace(/[\s,]/g, "").replace(/TZS/g, "") * 1
          : typeof i === "number"
          ? i
          : 0;

      const salesTotal = api
        .column(4)
        .data()
        .reduce((a, b) => intVal(a) + intVal(b), 0);

      const profitTotal = api
        .column(5)
        .data()
        .reduce((a, b) => intVal(a) + intVal(b), 0);

      $(api.column(4).footer())
        .html(this.formatCurrency(salesTotal))
        .addClass("text-end pe-3");

      $(api.column(5).footer())
        .html(this.formatCurrency(profitTotal))
        .addClass("text-end pe-3");
    };
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

        if (colIdx === 0 || colIdx === 1) {
          cell.html("");
        } else if (colIdx === 2) {
          const calendar = `
            <button type="button" class="btn btn-sm btn-primary text-white" 
                    data-bs-toggle="modal" data-bs-target="#date_filter_modal">
              <i class="fas fa-calendar-alt"></i>
            </button>
          `;
          cell.html(calendar);
        } else if (colIdx === 3) {
          const select = document.createElement("select");
          select.className = "select-filter text-charcoal float-start";
          select.innerHTML = `<option value="">All</option>`;
          $(this.selectors.shopsList)
            .find("option")
            .each((_, opt) => {
              select.innerHTML += `<option value="${$(opt).text()}">${$(
                opt
              ).text()}</option>`;
            });
          cell.html(select);
          $(select).on("change", () =>
            api.column(colIdx).search($(select).val()).draw()
          );
        } else {
          cell.html(
            "<input type='text' class='text-charcoal' placeholder='Filter..'/>"
          );
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
   * Setup row expansion for child rows
   */
  setupRowExpansion() {
    this.table.on("click", "td.dt-control", (e) => {
      const tr = e.target.closest("tr");
      const row = this.table.row(tr);
      const td = $(e.target).is("#reports_table tr td")
        ? $(e.target)
        : $(e.target).parent();

      if (row.child.isShown()) {
        row.child.hide();
        td.removeClass("text-danger").addClass("text-success");
        td.html(`<i class='fas fa-circle-chevron-right'></i>`);
      } else {
        row.child(this.formatRow(row.data()), "bg-white").show();
        td.removeClass("text-success").addClass("text-danger");
        td.html(`<i class='fas fa-circle-chevron-down'></i>`);
      }
    });
  }

  /**
   * Setup all event handlers
   */
  setupEventHandlers() {
    $(this.selectors.searchInput)
      .off("keyup")
      .on("keyup", () => {
        this.table.search($(this.selectors.searchInput).val()).draw();
      });

    $(this.selectors.clearFilter)
      .off("click")
      .on("click", (e) => {
        e.preventDefault();
        $(this.selectors.searchInput).val("");
        this.clearDates();
        $(".filters input[type='text']").val("");
        $(".filters select").val("");
        this.table.search("").columns().search("").draw();
      });

    $(this.selectors.dateClear)
      .off("click")
      .on("click", () => this.clearDates());

    $(this.selectors.dateFilterBtn)
      .off("click")
      .on("click", () => this.table.draw());
  }
}

// Initialize the application when DOM is ready
$(function () {
  new SalesReportManager();
});
