$(function () {
  var CSRF_TOKEN = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");

  function generate_errorsms(status, sms) {
    return `<div class="alert alert-${
      status ? "success" : "danger"
    } alert-dismissible fade show px-2 m-0 d-block w-100"><i class='fas fa-${status ? "check" : "exclamation"}-circle'></i> ${sms} <button type="button" class="btn-close d-inline-block" data-bs-dismiss="alert"></button></div>`;
  }

  $("#sales_table thead tr")
    .clone(true)
    .attr("class", "filters")
    .appendTo("#sales_table thead");

  var sales_table = $("#sales_table").DataTable({
    fixedHeader: true,
    processing: true,
    serverSide: true,
    ajax: {
      url: $("#sales_list_url").val(),
      type: "POST",
      dataType: "json",
      headers: { "X-CSRFToken": CSRF_TOKEN },
    },
    columns: [
      { data: "count" },
      { data: "name" },
      { data: "qty" },
      { data: "price" },
      { data: "sell_qty" },
      { data: "action" },
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
        targets: [0, 4, 5],
        orderable: false,
      },
      {
        targets: 1,
        className: "ellipsis text-start",
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var cell_content =
            `<a href="#" class="product-link">` +
            `<div class="product-info">` +
            `<div class="product-avatar">` +
            `<i class="fas fa-box-open"></i></div>` +
            `<span>${rowData.name}</span></div></a>`;
          $(cell).html(cell_content);
        },
      },
      {
        targets: [2, 3],
        className: "text-end pe-4",
      },
      {
        targets: 4,
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var cart = rowData.cart > 0 ? rowData.cart : "";
          var cell_content = `<input type="number" min="1" step="0.1" class="form-control" id="qty_${rowData.id}" max="${rowData.sell_qty}" value="${cart}" placeholder="Enter quantity.."/>`;
          $(cell).html(cell_content);
        },
      },
      {
        targets: 5,
        className: "align-middle text-nowrap text-center",
        createdCell: function (cell, cellData, rowData, rowIndex, colIndex) {
          var cell_content = `<button class="btn btn-success btn-sm" id="btn_${rowData.id}"><i class="fas fa-cart-plus"></i> Add</button>`;
          $(cell).html(cell_content);
        },
      },
    ],
    dom: "lBfrtip",
    buttons: [],
    initComplete: function () {
      var api = this.api();
      api
        .columns([0, 1, 2, 3, 4, 5])
        .eq(0)
        .each(function (colIdx) {
          var cell = $(".filters th").eq(
            $(api.column(colIdx).header()).index()
          );
          cell.addClass("bg-white");

          if (colIdx == 0 || colIdx == 4 || colIdx == 5) {
            cell.html("");
          } else {
            if (colIdx == 1) {
              $(cell).html(
                "<input type='text' class='text-color6 float-start' placeholder='Filter..'/>"
              );
            } else {
              $(cell).html(
                "<input type='text' class='text-color6 float-end' placeholder='Filter..'/>"
              );
            }
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

  $("#products_search").keyup(function () {
    sales_table.search($(this).val()).draw();
  });

  $("#filters_clear").click(function (e) {
    e.preventDefault();
    $("#products_search").val("");
    sales_table.search("").draw();
  });

  var btn_adding_cart = false;
  var btn_delete_cart = false;
  var cart_clearing = false;
  document.addEventListener("click", (e) => {
    var clicked = $(e.target);
    if (
      clicked.is("#sales_table tr td button") ||
      clicked.is("#sales_table tr td button i")
    ) {
      e.preventDefault();
      var row_id = clicked.is("#sales_table tr td button")
        ? clicked.attr("id").split("_")[1]
        : clicked.parent().attr("id").split("_")[1];
      var max_qty = parseFloat($("#qty_" + row_id).attr("max"));
      var val_qty = parseFloat($("#qty_" + row_id).val());
      if (val_qty > 0) {
        if (val_qty <= max_qty && btn_adding_cart == false) {
          $("#qty_" + row_id).css({
            border: "2px solid rgba(24, 132, 119, .6)",
            color: "#2D2D2D",
          });

          var formData = new FormData();
          formData.append("cart_add", "add_to_cart");
          formData.append("product", row_id);
          formData.append("qty", val_qty);

          var btn_clicked = clicked.is("#sales_table tr td button")
            ? clicked
            : clicked.parent();

          $.ajax({
            type: "POST",
            url: $("#cart_checkout_form").attr("action"),
            data: formData,
            dataType: "json",
            contentType: false,
            processData: false,
            headers: {
              "X-CSRFToken": CSRF_TOKEN,
            },
            beforeSend: function () {
              btn_adding_cart = true;
              btn_clicked.html(`<i class='fas fa-spinner fa-pulse'></i>`);
            },
            success: function (response) {
              btn_adding_cart = false;
              btn_clicked.html(`<i class="fas fa-cart-plus"></i> Add`);
              if (response.success) {
                $("#cart_items_btn").text(response.cart);
                $("#cart_checkout_form").load(
                  location.href + " #cart_checkout_form"
                );
                $("#confirm_sales_form").load(
                  location.href + " #confirm_sales_form"
                );
              } else {
                window.alert("Unknow error occured, reload & try again.");
              }
            },
            error: function (xhr, status, error) {
              btn_clicked.html(`<i class="fas fa-cart-plus"></i> Add`);
              window.alert("Unknow error occured, reload & try again.");
            },
          });
        } else {
          $("#qty_" + row_id).css({
            border: "1px solid #FF4444",
            color: "#FF4444",
          });
        }
      }
    } else if (
      clicked.is("#cart_checkout_form div span.del") ||
      clicked.is("#cart_checkout_form div span.del i")
    ) {
      var cart_id = clicked.is("#cart_checkout_form div span.del")
        ? clicked.attr("id").split("_")[1]
        : clicked.parent().attr("id").split("_")[1];
      if (btn_delete_cart == false) {
        var formData = new FormData();
        formData.append("cart_delete", parseInt(cart_id));

        var btn_clicked = clicked.is("#cart_checkout_form div span.del")
          ? clicked
          : clicked.parent();

        $.ajax({
          type: "POST",
          url: $("#cart_checkout_form").attr("action"),
          data: formData,
          dataType: "json",
          contentType: false,
          processData: false,
          headers: {
            "X-CSRFToken": CSRF_TOKEN,
          },
          beforeSend: function () {
            btn_delete_cart = true;
            btn_clicked.html(`<i class='fas fa-spinner fa-pulse'></i>`);
          },
          success: function (response) {
            btn_delete_cart = false;
            if (response.success) {
              $("#div_cart_" + cart_id).slideUp("fast");
              $("#cart_items_btn").text(response.cart);
              $("#grand_total_spn").text(response.grand_total);
              $("#confirm_sales_form").load(
                location.href + " #confirm_sales_form"
              );
              if (response.cart == 0)
                $("#cart_checkout_form").load(
                  location.href + " #cart_checkout_form"
                );
              sales_table.draw();
            } else {
              btn_clicked.html(`<i class="fas fa-trash-alt"></i>`);
              window.alert(response.sms);
            }
          },
          error: function (xhr, status, error) {
            btn_clicked.html(`<i class="fas fa-trash-alt"></i>`);
            window.alert("Failed to delete item, reload & try again");
          },
        });
      }
    } else if (clicked.is("#clear_cart_btn")) {
      if (cart_clearing == false) {
        var formData = new FormData();
        formData.append("clear_cart", "clear_cart");

        $.ajax({
          type: "POST",
          url: $("#cart_checkout_form").attr("action"),
          data: formData,
          dataType: "json",
          contentType: false,
          processData: false,
          headers: {
            "X-CSRFToken": CSRF_TOKEN,
          },
          beforeSend: function () {
            cart_clearing = true;
            clicked.html(`<i class='fas fa-spinner fa-pulse'></i>`);
          },
          success: function (response) {
            cart_clearing = false;
            if (response.success) {
              $("#cart_items_btn").text("0");
              sales_table.draw();
              $("#cart_checkout_form").load(
                location.href + " #cart_checkout_form"
              );
            } else {
              clicked.html(`Clear`);
              window.alert(response.sms);
            }
          },
          error: function (xhr, status, error) {
            btn_clicked.html(`Clear`);
            window.alert("Failed to clear items, reload & try again");
          },
        });
      }
    } else if (clicked.is("#checkoutModal_btn")) {
      if ($("#select_pay_type").val() == "") {
        $("#cart_checkout_form .formsms").html(
          generate_errorsms(false, "Please select payment type.")
        );
      } else {
        $("#confirm_checkout_modal").modal("show");
      }
    } else if (clicked.is("#checkout_confirm_btn")) {
      var formData = new FormData();
      formData.append("checkout", "checkout");
      formData.append("customer", $("#check_customerNames").val());
      formData.append("comment", $("#check_comment").val());

      $.ajax({
        type: "POST",
        url: $("#cart_checkout_form").attr("action"),
        data: formData,
        dataType: "json",
        contentType: false,
        processData: false,
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        },
        beforeSend: function () {
          $("#checkout_cancel_btn")
            .removeClass("d-inline-block")
            .addClass("d-none");
          $("#checkout_confirm_btn")
            .html("<i class='fas fa-spinner fa-pulse'></i>")
            .attr("type", "button");
        },
        success: function (response) {
          $("#checkout_cancel_btn")
            .removeClass("d-none")
            .addClass("d-inline-block");
          $("#checkout_confirm_btn").text("Continue").attr("type", "submit");
          if (response.success) {
            $("#cart_items_btn").text("0");
            sales_table.draw();
            $("#cart_checkout_form").load(
              location.href + " #cart_checkout_form"
            );
            $("#checkout_confirm_btn")
              .removeClass("d-inline-block")
              .addClass("d-none");
            $("#confirm_sales_form .form-floating")
              .removeClass("text-color5")
              .addClass("text-color2");
            $("#confirm_sales_form .form-floating").html(
              `<i class="fas fa-check-circle"></i> &nbsp; ${response.sms}`
            );
          } else {
            $("#confirm_sales_form .formsms").html(
              generate_errorsms(response.success, response.sms)
            );
          }
        },
        error: function (xhr, status, error) {
          $("#checkout_cancel_btn")
            .removeClass("d-none")
            .addClass("d-inline-block");
          $("#checkout_confirm_btn").text("Save").attr("type", "submit");
          $("#confirm_sales_form .formsms").html(
            generate_errorsms(false, "Failed to checkout, reload & try again")
          );
        },
      });
    }
  });
});
