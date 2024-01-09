odoo.define('yena_quality_development.UrlViewerWidget', function(require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var UrlViewerWidget = AbstractField.extend({
        template: 'UrlViewerWidgetTemplate',

        _render: function() {

            console.log("Rendering URL Viewer with value:", this.value); // Bu satırı ekleyin
            var url = this.value;
            console.log("deneme",url)
            if (url) {
                var display_text = decodeURIComponent(url.split('/').pop()); // Decode and get the last part of the URL
                console.log(display_text)
                var linkHtml = '<a href="' + url + '" target="_blank">' + display_text + '</a>';               
                this.$el.html(linkHtml);
            } else {
                this.$el.empty();  // Clear the HTML content if URL is not available
            }
        }
    });

    fieldRegistry.add('url_viewer', UrlViewerWidget);

    return UrlViewerWidget;
});
