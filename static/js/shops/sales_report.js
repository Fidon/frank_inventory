$(function () {
  $("#sales_toggle").click();

  var CSRF_TOKEN = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
  const COLUMN_INDICES = [0, 1, 2, 3, 4, 5, 6];
  const SHOP_OPTIONS = $("#shops_list option");
  const DATE_CACHE = { start: null, end: null };

  function generate_errorsms(status, sms) {
    return `<div class="alert alert-${
      status ? "success" : "danger"
    } alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-${status ? "check" : "exclamation"}-circle'></i> ${sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
  }

  function getDateRange() {
    const minDateStr = $("#min_date").val();
    const maxDateStr = $("#max_date").val();

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

      // Cache the results
      DATE_CACHE.start = dtStartUtc;
      DATE_CACHE.end = dtEndUtc;

      return { start: dtStartUtc, end: dtEndUtc };
    } catch (error) {
      console.error("Date processing error:", error);
      return { start: null, end: null };
    }
  }

  function clearDates() {
    $("#min_date").val("");
    $("#max_date").val("");
    DATE_CACHE.start = null;
    DATE_CACHE.end = null;
  }

  function format_row(d) {
    let row_contents = ``;
    let items = d.items;
    items.forEach((item) => {
      row_contents +=
        `<div class="d-block w-100 float-start text-start my-1 px-2">` +
        `<span class="d-inline-block px-1">${item.count}.</span>` +
        `<span class="d-inline-block px-1 mx-1">${item.names}</span>` +
        `<span class="d-inline-block px-1 mx-1">${item.price} (${item.qty})</span>` +
        `<span class="d-inline-block px-1">= &nbsp; ${item.total}</span>` +
        `</div>`;
    });
    return row_contents;
  }

  function formatCurrency(num) {
    return (
      num.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) + " TZS"
    );
  }

  $("#reports_table thead tr")
    .clone(true)
    .attr("class", "filters")
    .appendTo("#reports_table thead");
  var reports_table = $("#reports_table").DataTable({
    fixedHeader: true,
    processing: true,
    serverSide: true,
    ajax: {
      url: $("#sales_report_url").val(),
      type: "POST",
      data: function (d) {
        const dateRange = getDateRange();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": CSRF_TOKEN },
      dataSrc: function (json) {
        var tableFooter = $("#reports_table tfoot");
        $(tableFooter).find("tr").eq(1).find("th").eq(4).html(json.grand_total);
        return json.data;
      },
    },
    columns: [
      {
        className: "dt-control text-success",
        data: null,
        defaultContent: `<i class='fas fa-circle-chevron-right'></i>`,
      },
      { data: "count" },
      { data: "saledate" },
      { data: "shop" },
      { data: "amount" },
      { data: "customer" },
      { data: "user" },
    ],
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
    columnDefs: [
      {
        targets: [0, 1],
        orderable: false,
      },
      {
        targets: 4,
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          $(cell).attr("class", "text-end pe-4");
        },
      },
      {
        targets: 5,
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          $(cell).attr("class", "ellipsis text-start ps-1");
        },
      },
      {
        targets: 6,
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          $(cell).attr("class", "ellipsis text-start ps-1");
        },
      },
    ],
    buttons: [
      {
        // Copy button
        extend: "copy",
        text: "<i class='fas fa-clone'></i>",
        className: "btn btn-extra text-white",
        titleAttr: "Copy",
        title: "Sales report - FrankApp",
        exportOptions: {
          columns: [1, 2, 3, 4, 5, 6],
        },
      },
      {
        // PDF button
        extend: "pdf",
        text: "<i class='fas fa-file-pdf'></i>",
        className: "btn btn-extra text-white",
        titleAttr: "Export to PDF",
        title: "Sales report - FrankApp",
        filename: "sales-report",
        orientation: "landscape",
        pageSize: "A4",
        footer: true,
        exportOptions: {
          columns: [1, 2, 3, 4, 5, 6],
          search: "applied",
          order: "applied",
        },
        tableHeader: {
          alignment: "center",
        },
        customize: function (doc) {
          doc.styles.tableHeader.alignment = "center";
          doc.styles.tableBodyOdd.alignment = "center";
          doc.styles.tableBodyEven.alignment = "center";
          doc.styles.tableHeader.fontSize = 11;
          doc.defaultStyle.fontSize = 11;
          doc.content[1].table.widths = Array(
            doc.content[1].table.body[1].length + 1
          )
            .join("*")
            .split("");

          var body = doc.content[1].table.body;
          for (i = 1; i < body.length; i++) {
            doc.content[1].table.body[i][0].margin = [3, 0, 0, 0];
            doc.content[1].table.body[i][0].alignment = "center";
            doc.content[1].table.body[i][1].alignment = "center";
            doc.content[1].table.body[i][2].alignment = "center";
            doc.content[1].table.body[i][3].alignment = "right";
            doc.content[1].table.body[i][3].padding = [0, 10, 0, 0];
            doc.content[1].table.body[i][4].alignment = "left";
            doc.content[1].table.body[i][5].alignment = "left";
            doc.content[1].table.body[i][5].margin = [0, 0, 3, 0];

            for (let j = 0; j < body[i].length; j++) {
              body[i][j].style = "vertical-align: middle;";
            }
          }
        },
      },
      {
        // Export to excel button
        extend: "excel",
        text: "<i class='fas fa-file-excel'></i>",
        className: "btn btn-extra text-white",
        titleAttr: "Export to Excel",
        title: "Sales report - FrankApp",
        exportOptions: {
          columns: [1, 2, 3, 4, 5, 6],
        },
      },
      {
        // Print button
        extend: "print",
        text: "<i class='fas fa-print'></i>",
        className: "btn btn-extra text-white",
        title: "Sales report - FrankApp",
        orientation: "landscape",
        pageSize: "A4",
        titleAttr: "Print",
        footer: true,
        exportOptions: {
          columns: [1, 2, 3, 4, 5, 6],
          search: "applied",
          order: "applied",
        },
        tableHeader: {
          alignment: "center",
        },
        customize: function (win) {
          $(win.document.body).css("font-size", "11pt");
          $(win.document.body)
            .find("table")
            .addClass("compact")
            .css("font-size", "inherit");
        },
      },
    ],
    footerCallback: function (row, data, start, end, display) {
      var api = this.api(),
        data;
      var intVal = function (i) {
        return typeof i === "string"
          ? i.replace(/[\s,]/g, "").replace(/TZS/g, "") * 1
          : typeof i === "number"
          ? i
          : 0;
      };
      var salesTotal = api
        .column(4)
        .data()
        .reduce(function (a, b) {
          return intVal(a) + intVal(b);
        }, 0);

      $(api.column(4).footer()).html(formatCurrency(salesTotal));
    },
    initComplete: function () {
      var api = this.api();
      api
        .columns(COLUMN_INDICES)
        .eq(0)
        .each(function (colIdx) {
          var cell = $(".filters th").eq(
            $(api.column(colIdx).header()).index()
          );
          cell.addClass("bg-white");

          if (colIdx == 2) {
            var calendar = `<button type="button" class="btn btn-sm btn-primary text-white" data-bs-toggle="modal" data-bs-target="#date_filter_modal"><i class="fas fa-calendar-alt"></i></button>`;
            cell.html(calendar);
          } else if (colIdx == 3) {
            var select = document.createElement("select");
            select.className = "select-filter text-charcoal float-start";
            select.innerHTML = `<option value="">All</option>`;
            SHOP_OPTIONS.each(function () {
              select.innerHTML += `<option value="${$(this).text()}">${$(
                this
              ).text()}</option>`;
            });
            cell.html(select);
            $(select).on("change", function () {
              api.column(colIdx).search($(this).val()).draw();
            });
          } else if (colIdx == 0 || colIdx == 1) {
            cell.html("");
          } else {
            $(cell).html(
              "<input type='text' class='text-charcoal' placeholder='Filter..'/>"
            );
            $(
              "input",
              $(".filters th").eq($(api.column(colIdx).header()).index())
            )
              .off("keyup change")
              .on("keyup change", function (e) {
                e.stopPropagation();
                $(this).attr("title", $(this).val());
                var regexr = "{search}";
                var cursorPosition = this.selectionStart;
                api
                  .column(colIdx)
                  .search(
                    this.value != ""
                      ? regexr.replace("{search}", this.value)
                      : "",
                    this.value != "",
                    this.value == ""
                  )
                  .draw();
                $(this)
                  .focus()[0]
                  .setSelectionRange(cursorPosition, cursorPosition);
              });
          }
        });
    },
  });

  reports_table.on("click", "td.dt-control", function (e) {
    let tr = e.target.closest("tr");
    let row = reports_table.row(tr);
    let td = $(e.target).is("#reports_table tr td")
      ? $(e.target)
      : $(e.target).parent();

    if (row.child.isShown()) {
      row.child.hide();
      td.removeClass("text-danger").addClass("text-success");
      td.html(`<i class='fas fa-circle-chevron-right'></i>`);
    } else {
      row.child(format_row(row.data()), "bg-white").show();
      td.removeClass("text-success").addClass("text-danger");
      td.html(`<i class='fas fa-circle-chevron-down'></i>`);
    }
  });

  // Event handlers on user search and date filtering
  $("#sales_search")
    .off("keyup")
    .on("keyup", function () {
      reports_table.search($(this).val()).draw();
    });

  $("#sales_filter_clear")
    .off("click")
    .on("click", function (e) {
      e.preventDefault();
      $("#sales_search").val("");
      clearDates();
      $(".filters input[type='text']").val("");
      $(".filters select").val("");
      reports_table.columns().search("").draw();
    });

  $("#date_clear")
    .off("click")
    .on("click", function () {
      clearDates();
    });

  $("#date_filter_btn")
    .off("click")
    .on("click", function () {
      reports_table.draw();
    });
});
