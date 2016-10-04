window.core = {};

(function($, undefined) {

    core.Modal = function(params) {

        var opts = {
            show_action_btn: false,
            on_url_loaded: function() {},
            size: 'lg',
        }

        this.init = function(params) {
            this.modal = $('#dynamicModal');
            this.options = $.extend({}, opts, params);
            this.setStyle();
            this.setTitle();
            this.setContent();
            this.setButtons();
        };

        this.setStyle = function() {

            if(typeof this.options.style != 'undefined') {
                this.modal.addClass(this.options.style);
            }

            this.modal.find('.modal-dialog').addClass('modal-' + this.options.size);

        };

        this.setTitle = function() {

            if(typeof this.options.title != 'undefined') {
                this.modal.find('.modal-title').html(this.options.title);
            }

        };

        this.setContent = function() {
            var self = this;
            if(typeof this.options.url != 'undefined') {
                this.method = 'request';
                $.get(this.options.url, function(response) {
                    self.modal.find('.modal-body').html(response);
                    self.options.on_url_loaded(self);
                })
            }
            else if(typeof this.options.content != 'undefined') {
                self.modal.find('.modal-body').html(this.options.content);
            }
        };

        this.setButtons = function() {

            if(typeof this.options.show_action_btn != 'undefined' && this.options.show_action_btn ) {
            }
            else {
                $('.btn-action').hide();
            }
        };

        this.open = function() {
            this.modal.modal();
        };

        this.init(params);
    }

})(jQuery, undefined)
