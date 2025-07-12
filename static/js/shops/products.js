$(function () {
  const CSRF_TOKEN = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
  const COLUMN_INDICES = [0, 1, 2, 3, 4, 5, 6];
  const SHOP_OPTIONS = $("#item_shop option");
  const DATE_CACHE = { start: null, end: null };

  function generate_errorsms(status, sms) {
    return `<div class="alert alert-${
      status ? "success" : "danger"
    } alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-${status ? "check" : "exclamation"}-circle'></i> ${sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
  }

  // New shop item/product registration & update
  $("#new_product_form").submit(function (e) {
    e.preventDefault();

    $.ajax({
      type: "POST",
      url: $(this).attr("action"),
      data: new FormData($(this)[0]),
      dataType: "json",
      contentType: false,
      processData: false,
      headers: {
        "X-CSRFToken": CSRF_TOKEN,
      },
      beforeSend: function () {
        $("#product_cancel_btn")
          .removeClass("d-inline-block")
          .addClass("d-none");
        $("#product_submit_btn")
          .html("<i class='fas fa-spinner fa-pulse'></i> Saving")
          .attr("type", "button");
      },
      success: function (response) {
        $("#product_cancel_btn")
          .removeClass("d-none")
          .addClass("d-inline-block");
        $("#product_submit_btn").text("Save").attr("type", "submit");

        var fdback = generate_errorsms(response.success, response.sms);

        $("#new_product_canvas .offcanvas-body").animate(
          { scrollTop: 0 },
          "slow"
        );
        $("#new_product_form .formsms").html(fdback);

        if (response.update_success) {
          $("#product_div").load(location.href + " #product_div");
          $("html, body").animate({ scrollTop: 0 }, "slow");
        } else if (response.success) {
          $("#new_product_form")[0].reset();
          products_table.draw();
        }
      },
      error: function (xhr, status, error) {
        $("#product_cancel_btn")
          .removeClass("d-none")
          .addClass("d-inline-block");
        $("#product_submit_btn").text("Save").attr("type", "submit");
        var fdback = generate_errorsms(false, "Unknown error, reload & try");
        $("#new_product_canvas .offcanvas-body").animate(
          { scrollTop: 0 },
          "slow"
        );
        $("#new_product_form .formsms").html(fdback);
      },
    });
  });

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

  // Shops table initialization
  $("#products_table thead tr")
    .clone(true)
    .attr("class", "filters")
    .appendTo("#products_table thead");

  var products_table = $("#products_table").DataTable({
    fixedHeader: true,
    processing: true,
    serverSide: true,
    ajax: {
      url: $("#products_list_url").val(),
      type: "POST",
      data: function (d) {
        const dateRange = getDateRange();
        d.startdate = dateRange.start;
        d.enddate = dateRange.end;
      },
      dataType: "json",
      headers: { "X-CSRFToken": CSRF_TOKEN },
    },
    columns: [
      { data: "count" },
      { data: "name" },
      { data: "shop" },
      { data: "qty" },
      { data: "cost" },
      { data: "price" },
      { data: "status" },
    ],
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
    columnDefs: [
      {
        targets: 0,
        orderable: false,
      },
      {
        targets: 1,
        className: "ellipsis text-start",
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var cell_content =
            `<a href="${rowData.info}" class="product-link">` +
            `<div class="product-info">` +
            `<div class="product-avatar">` +
            `<i class="fas fa-box-open"></i></div>` +
            `<span>${rowData.name}</span></div></a>`;
          $(cell).html(cell_content);
        },
      },
      {
        targets: [4, 5],
        className: "text-end pe-3",
      },
      {
        targets: 6,
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          if (rowData.status == "Active") {
            $(cell).addClass("text-success");
          } else {
            $(cell).addClass("text-danger");
          }
        },
      },
    ],
    dom: "lBfrtip",
    buttons: [
      {
        // Copy button
        extend: "copy",
        text: "<i class='fas fa-clone'></i>",
        className: "btn btn-extra text-white",
        titleAttr: "Copy",
        title: "Shop items - FrankApp",
        exportOptions: {
          columns: COLUMN_INDICES,
        },
      },
      {
        // PDF button
        extend: "pdf",
        text: "<i class='fas fa-file-pdf'></i>",
        className: "btn btn-extra text-white",
        titleAttr: "Export to PDF",
        title: "Shop items - FrankApp",
        filename: "shopitems-frankapp",
        orientation: "portrait",
        pageSize: "A4",
        footer: true,
        exportOptions: {
          columns: COLUMN_INDICES,
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
          doc.styles.tableHeader.fontSize = 7;
          doc.defaultStyle.fontSize = 6;
          doc.content[1].table.widths = Array(
            doc.content[1].table.body[1].length + 1
          )
            .join("*")
            .split("");

          var body = doc.content[1].table.body;
          for (i = 1; i < body.length; i++) {
            doc.content[1].table.body[i][0].margin = [3, 0, 0, 0];
            doc.content[1].table.body[i][0].alignment = "center";
            doc.content[1].table.body[i][1].alignment = "left";
            doc.content[1].table.body[i][2].alignment = "center";
            doc.content[1].table.body[i][3].alignment = "center";
            doc.content[1].table.body[i][4].alignment = "right";
            doc.content[1].table.body[i][5].alignment = "right";
            doc.content[1].table.body[i][6].alignment = "center";
            doc.content[1].table.body[i][6].margin = [0, 0, 3, 0];

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
        title: "Shop items - FrankApp",
        exportOptions: {
          columns: COLUMN_INDICES,
        },
      },
      {
        // Print button
        extend: "print",
        text: "<i class='fas fa-print'></i>",
        className: "btn btn-extra text-white",
        title: "Shop items - FrankApp",
        orientation: "portrait",
        pageSize: "A4",
        titleAttr: "Print",
        footer: true,
        exportOptions: {
          columns: COLUMN_INDICES,
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

          if (colIdx == 0) {
            $(cell).html("");
          } else if (colIdx == 2) {
            var select = document.createElement("select");
            select.className = "select-filter text-charcoal float-start";
            select.innerHTML = `<option value="">All</option>`;
            SHOP_OPTIONS.each(function (index) {
              if (index === 0) return;
              select.innerHTML += `<option value="${$(this).text()}">${$(
                this
              ).text()}</option>`;
            });
            cell.html(select);
            $(select).on("change", function () {
              api.column(colIdx).search($(this).val()).draw();
            });
          } else if (colIdx == 6) {
            var select = document.createElement("select");
            select.className = "select-filter text-charcoal float-start";
            select.innerHTML =
              `<option value="">All</option>` +
              `<option value="Active">Active</option>` +
              `<option value="Blocked">Blocked</option>` +
              `<option value="SoldOut">SoldOut</option>`;
            cell.html(select);
            $(select).on("change", function () {
              api.column(colIdx).search($(this).val()).draw();
            });
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

  // Event handlers on user search and date filtering
  $("#products_search")
    .off("keyup")
    .on("keyup", function () {
      products_table.search($(this).val()).draw();
    });

  $("#products_filter_clear")
    .off("click")
    .on("click", function (e) {
      e.preventDefault();
      $("#products_search").val("");
      $(".filters input[type='text']").val("");
      $(".filters select").val("");
      products_table.columns().search("").draw();
    });

  // Delete confirmation modal
  var btn_deleting = false;
  $("#confirm_delete_btn").click(function (e) {
    e.preventDefault();
    if (btn_deleting == false) {
      var formData = new FormData();
      formData.append("delete_product", $("#get_product_id").val());

      $.ajax({
        type: "POST",
        url: $("#new_product_form").attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
        beforeSend: function () {
          btn_deleting = true;
          $("#cancel_delete_btn")
            .removeClass("d-inline-block")
            .addClass("d-none");
          $("#confirm_delete_btn").html(
            "<i class='fas fa-spinner fa-pulse'></i>"
          );
        },
        success: function (response) {
          btn_deleting = false;
          if (response.success) {
            window.alert("The item/product has been deleted permanently..!");
            window.location.href = response.url;
          } else {
            $("#cancel_delete_btn")
              .removeClass("d-none")
              .addClass("d-inline-block");
            $("#confirm_delete_btn").html(
              "<i class='fas fa-check-circle'></i> Yes"
            );

            var fdback = generate_errorsms(response.success, response.sms);

            $("#confirm_delete_modal .formsms").html(fdback);
          }
        },
        error: function (xhr, status, error) {
          console.log(error);
        },
      });
    }
  });

  //   Hide/Unhide product from shop
  var btn_blocking = false;
  $("#item_blockbtn").click(function (e) {
    e.preventDefault();
    if (btn_blocking == false) {
      var btn_html = $(this).html();
      var formdata = new FormData();
      formdata.append("block_product", parseInt($("#get_product_id").val()));

      $.ajax({
        type: "POST",
        url: $("#new_product_form").attr("action"),
        data: formdata,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
        beforeSend: function () {
          btn_blocking = true;
          $("#item_blockbtn").html(
            "<i class='fas fa-spinner fa-pulse'></i>Updating"
          );
        },
        success: function (response) {
          btn_blocking = false;
          if (response.success) {
            location.reload();
          } else {
            $("#item_blockbtn").html(btn_html);
            window.alert("Operation failed, reload and try again");
          }
        },
        error: function (xhr, status, error) {
          console.log(error);
        },
      });
    }
  });

  // Qty update modal
  var btn_qty = false;
  $("#newqty_addbtn").click(function (e) {
    e.preventDefault();
    var check_qty = $("#item_new_qty").val();
    if (check_qty !== "" && check_qty >= 1) {
      if (btn_qty == false) {
        var formData = new FormData();
        formData.append("qty_product", $("#get_product_id").val());
        formData.append("qty_new", $("#item_new_qty").val());

        $.ajax({
          type: "POST",
          url: $("#new_product_form").attr("action"),
          data: formData,
          dataType: "json",
          contentType: false,
          processData: false,
          headers: {
            "X-CSRFToken": CSRF_TOKEN,
          },
          beforeSend: function () {
            btn_qty = true;
            $("#newqty_cancelbtn")
              .removeClass("d-inline-block")
              .addClass("d-none");
            $("#newqty_addbtn").html(
              "<i class='fas fa-spinner fa-pulse'></i> Adding"
            );
          },
          success: function (response) {
            btn_qty = false;
            var fdback = generate_errorsms(response.success, response.sms);

            if (response.success) {
              var qty =
                parseFloat($("#item_new_qty").val()) +
                parseFloat($("#item_up_qty").val());
              $("#item_up_qty").val(qty);
              $("#item_new_qty").val("");

              $("#product_div").load(location.href + " #product_div");
            }
            $("#newqty_cancelbtn")
              .removeClass("d-none")
              .addClass("d-inline-block");
            $("#newqty_addbtn").html("<i class='fas fa-check-circle'></i> Add");
            $("#new_qty_modal .formsms").html(fdback);
          },
          error: function (xhr, status, error) {
            console.log(error);
          },
        });
      }
    } else {
      var fdback = generate_errorsms(
        false,
        "New quantity should be 1 or more."
      );
      $("#new_qty_modal .formsms").html(fdback);
    }
  });
});
