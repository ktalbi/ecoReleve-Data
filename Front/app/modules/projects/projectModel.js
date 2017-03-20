define([
	'backbone'
], function(Backbone) {

  'use strict';

  return Backbone.Model.extend({
    schema: {
      
      name: {
        type: 'Text' ,
        title: 'Nom du projet',
        editorClass: 'form-control',
        validators: ['required']
      },
      refCustomer: {
        type: 'Text' ,
        title: 'Référence client',
        editorClass: 'form-control',
        validators: []
      },
      description: {
        type: 'Text' ,
        title: 'Description',
        editorClass: 'form-control',
        validators: []
      },
      file: {
        type: 'FileUploadEditor',
        title: 'Emprise géographique (shp,kml, geojson)',
        editorClass: 'form-control',
				fieldClass: 'filesinputselector',
        validators: [],
        options: {extensions: null}
      },


    }
  });
});
