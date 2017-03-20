define([
  'jquery',
  'underscore',
  'backbone',
  'marionette',
  'moment',
  'sweetAlert',
  'ns_form/NSFormsModuleGit',
  './projectModel',
  'ns_map/ns_map',
  'i18n'

], function(
  $, _, Backbone, Marionette,
  moment, Swal,
  NsForm,ProjectModel, NsMap
){

  'use strict';

  return Marionette.LayoutView.extend({
    template: 'app/modules/projects/tpl-new-project.html',
    className: 'full-height white',

    events: {

      'click .js-btn-save': 'save',


    },


    ui: {
      'projForm': '.js-form',
    },

    initialize: function(options) {

    },

    onShow: function() {
      this.displayForm();
      this.$el.i18n();
    },

    onDestroy: function() {
      //this.map.destroy();
      this.nsForm.destroy();
    },

    save: function() {
      this.nsForm.butClickSave();
    }, 
    displayForm: function() {
      var self = this;
      //var model = new ProjectModel();
      this.nsForm = new NsForm({
        name: 'ProjForm',
        modelurl: 'projects/',
        //model: model,
        buttonRegion: [],
        formRegion: self.ui.projForm,
        displayMode: 'edit',
        id: 0,
      });
    },

  });
});
