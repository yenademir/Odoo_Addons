odoo.define('purchase_portal.custom_functionality', function (require) {
    'use strict';

    var rpc = require('web.rpc');

    function updateGrandTotal() {
        var grandTotal = 0;
        // Tüm subtotal değerlerini dön ve topla
        $('span.subtotal').each(function() {
            var value = parseFloat($(this).text()) || 0;
            grandTotal += value;
        });
        // Toplam alt toplamı güncelle
        $('#grand_total').text('Toplam: ' + grandTotal.toFixed(2));
    }

    $(document).on('input', 'input[name="custom_price"]', function() {
        var $input = $(this);
        var price = parseFloat($input.val()) || 0;
        var $row = $input.closest('tr');
        var quantity = parseFloat($row.find('span.product_qty').text()) || 0;
        var subtotal = price * quantity;

        // Subtotal değerini güncelle
        $row.find('span.subtotal').text(subtotal.toFixed(2));

        // Tüm satırların yeni subtotal değerleriyle toplam alt toplamı güncelle
        updateGrandTotal();
    });

    // Sayfa yüklendiğinde veya başka bir event sonrası ilk toplam subtotal hesaplaması için bu fonksiyonu çağırabilirsiniz.
    updateGrandTotal();

    $(document).ready(function () {
        $('body').on('click', '.send-purchase-data', function (e) {
            var allValid = true;
            var customPrices = [];
            var customDates = [];
            var customCurrency = $("select[name='custom_currency']").val();

            $("input[name='custom_price']").each(function() {
                var price = $(this).val();
                var priceSituationChecked = $(this).closest('tr').find('.price-situation-checkbox').prop('checked');

                if (!priceSituationChecked && price == 0) {
                    allValid = false;
                    alert("Fiyat 0 olamaz, lütfen fiyatı doldurun.");
                    return false;
                }
                customPrices.push(price);
            });

            $("input[name='custom_date']").each(function() {
                // Tarihi al
                var date = $(this).val();
                // Tarih girilmemişse null veya boş string olarak diziye ekle
                customDates.push(date || '');
            });

            if (allValid) {
                var orderId = $(this).data('order-id');

                rpc.query({
                    model: 'purchase.order',
                    method: 'update_custom_data_portal',
                    args: [orderId, customPrices, customDates, customCurrency],
                }).then(function (result) {
                    if (result.success) {
                        window.location.reload();
                    } else {
                        alert("There was an error updating the data.");
                    }
                }).catch(function (error) {
                    alert("There was an unexpected error.");
                    console.log("RPC Error:", error);
                });
            }
        });

        $('body').on('click', '.price-situation-checkbox', function (e) {
            var isChecked = $(this).prop('checked');

            $(this).closest('tr').find('input[name="custom_price"]').prop('required', !isChecked);
        });
    });
});
