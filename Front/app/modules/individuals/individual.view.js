define([
  'jquery',
  'underscore',
  'backbone',
  'marionette',

  'sweetAlert',
  'translater',

  './individual.model',
  'modules/objects/detail.view',

  'ns_map/ns_map',
  'ns_form/NSFormsModuleGit',
  'ns_grid/grid.view',

], function(
  $, _, Backbone, Marionette,
  Swal, Translater, IndividualModel, DetailView,
  NsMap, NsForm, GridView
){

  'use strict';

  return DetailView.extend({
    className: 'individual full-height animated white',

    events: {
      'click .tab-link': 'displayTab',
      'click button.js-btn-delete-locations': 'warnDeleteLocations',
    },

    ModelPrototype: IndividualModel,

    onShow: function() {
      DetailView.prototype.onShow.call(this);
      $('.js-form-btns').hide();
    },

    displayMap: function() {
      var _this = this;
      this.map = new NsMap({
        url: this.model.get('type') + '/' + this.model.get('id')  + '/locations?geo=true',
        cluster: true,
        legend: true,
        zoom: 3,
        element: 'map',
        popup: true,
        com: this.com,
        selection: true,
        //bbox: true,
      });

      $.when(this.map.google.defered).then(
        function(){
          _this.map.url = false;
        }
      );
    },

    displayGrids: function() {
      this.displayHistoryGrid();
      this.displayEquipmentGrid();
      this.displayLocationsGrid();
    },

    displayHistoryGrid: function() {
      this.rgHistoryGrid.show(this.historyGrid = new GridView({
        columns: this.model.get('historyColumnDefs'),
        type: this.model.get('type'),
        url: this.model.get('type') + '/' + this.model.get('id')  + '/history',
        clientSide: true,
        gridOptions : {
          rowHeight : 30,
          rowClass: 'line-30'
        }
      }));
      this.gridViews.push(this.historyGrid);
    },

    displayEquipmentGrid: function() {
      this.rgEquipmentGrid.show(this.equipmentGrid = new GridView({
        columns: this.model.get('equipmentColumnDefs'),
        type: this.model.get('type'),
        url: this.model.get('type') + '/' + this.model.get('id')  + '/equipment',
        clientSide: true,
        gridOptions : {
          rowHeight : 30,
          rowClass: 'line-30'
        }
      }));
      this.gridViews.push(this.equipmentGrid);
    },

    displayLocationsGrid: function() {
      var _this = this;
      this.rgLocationsGrid.show(this.locationsGrid = new GridView({
        com: this.com,
        columns: this.model.get('locationsColumnDefs'),
        type: this.model.get('type'),
        url: this.model.get('type') + '/' + this.model.get('id')  + '/locations',
        clientSide: true,
        gridOptions: {
          rowSelection: 'multiple',
          enableFilter: true,
          rowHeight : 30,
          rowClass: 'line-30',
          onRowClicked: function(row){
            _this.locationsGrid.interaction('focus', row.data.ID || row.data.id);
          }
        }
      }));
      this.gridViews.push(this.locationsGrid);
    },

    warnDeleteLocations: function() {
      var _this = this;
      var selectedNodes = this.locationsGrid.gridOptions.api.getSelectedNodes();
      if(!selectedNodes.length){
        return;
      }

      var callback = function() {
        _this.deleteLocations(selectedNodes);
      };
      var opt = {
        title: 'Are you sure?',
        text: 'selected locations will be deleted'
      };
      this.swal(opt, 'warning', callback);
    },

    deleteLocations: function(selectedNodes) {
      var _this = this;
      var url = this.model.get('type') + '/' + this.model.get('id')  + '/locations';

      var selectedIds = selectedNodes.map(function(node){
        return node.data.ID;
      });

      $.ajax({
        url: url,
        method: 'PUT',
        data: {'IDs': JSON.stringify(selectedIds)},
        context: this,
      }).done(function(resp) {
        this.locationsGrid.gridOptions.api.removeItems(selectedNodes);
        this.locationsGrid.clientSideFilter();
      }).fail(function(resp) {
        this.swal(resp, 'error');
      });
    },

    swal: function(opt, type, callback) {
      var btnColor;
      switch (type){
        case 'success':
          btnColor = 'green';
          opt.title = 'Success';
          break;
        case 'error':
          btnColor = 'rgb(147, 14, 14)';
          opt.title = 'Error';
          break;
        case 'warning':
          if (!opt.title) {
            opt.title = 'warning';
          }
          btnColor = 'orange';
          break;
        default:
          return;
          break;
      }

      Swal({
        title: opt.title,
        text: opt.text || '',
        type: type,
        showCancelButton: true,
        confirmButtonColor: btnColor,
        confirmButtonText: 'OK',
        closeOnConfirm: true,
      },
      function(isConfirm) {
        //could be better
        if (isConfirm && callback) {
          callback();
        }
      });
    },
  });
});
