from pyramid.view import view_config
from ..Models import (
    Station,
    StationType,
    Station_FieldWorker,
    StationList,
    MonitoredSitePosition
)
from ..GenericObjets.FrontModules import FrontModules, ModuleForms
from ..GenericObjets import ListObjectWithDynProp
import json
import itertools
from datetime import datetime
import pandas as pd
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
import io
from pyramid.response import Response
from ..controllers.security import routes_permission
from collections import OrderedDict


PREFIX = 'stations'


@view_config(
    route_name=PREFIX + '/action',
    renderer='json',
    request_method='GET',
    permission=routes_permission[PREFIX]['GET'])
def actionOnStations(request):
    dictActionFunc = {
        'count': count_,
        'forms': getForms,
        '0': getForms,
        'getFields': getFields,
        'getFilters': getFilters,
        'getType': getStationType,
        'updateSiteLocation': updateMonitoredSite,
        'importGPX': getFormImportGPX
    }
    actionName = request.matchdict['action']
    return dictActionFunc[actionName](request)


def count_(request=None, listObj=None):
    if request is not None:
        data = request.params
        searchInfo = {}
        if 'criteria' in data:
            data['criteria'] = json.loads(data['criteria'])
            if data['criteria'] != {}:
                searchInfo['criteria'] = [obj for obj in data[
                    'criteria'] if obj['Value'] != str(-1)]

        listObj = ListObjectWithDynProp(Station)
        count = listObj.count(searchInfo=searchInfo)
    else:
        count = listObj.count()
    return count


def getFilters(request):
    moduleName = request.params.get('FilterName', None)
    filtersList = Station().GetFilters(moduleName)
    filters = {}
    for i in range(len(filtersList)):
        filters[str(i)] = filtersList[i]

    return filters


def getForms(request):
    session = request.dbsession
    typeSta = request.params['ObjectType']
    ModuleName = 'StationForm'
    Conf = session.query(FrontModules).filter(
        FrontModules.Name == ModuleName).first()
    newSta = Station(FK_StationType=typeSta)
    newSta.init_on_load()
    schema = newSta.GetDTOWithSchema(Conf, 'edit')

    return schema


def getFields(request):
    ModuleType = 'StationGrid'
    cols = Station().GetGridFields(ModuleType)

    return cols


def getStationType(request):
    session = request.dbsession
    query = select([StationType.ID.label('val'),
                    StationType.Name.label('label')])
    response = [OrderedDict(row) for row in session.execute(query).fetchall()]

    return response


def getFormImportGPX(request):
    session = request.dbsession
    conf = session.query(FrontModules).filter(
        FrontModules.Name == 'ImportFileForm').first()
    response = {'schema': {}}
    inputs_ = session.query(ModuleForms).filter(ModuleForms.Module_ID == conf.ID).filter(
        ModuleForms.TypeObj == 1).order_by(ModuleForms.FormOrder.asc()).all()
    for input_ in inputs_:
        response['schema'][input_.Name] = input_.GetDTOFromConf(True)

    resultat = []
    Legends = sorted([
        (obj.Legend, obj.FormOrder, obj.Name)
        for obj in inputs_ if obj.FormOrder is not None],
            key=lambda x: x[1])
    Unique_Legends = list()
    for x in Legends:
        if x[0] not in Unique_Legends:
            Unique_Legends.append(x[0])

    for curLegend in Unique_Legends:
        curFieldSet = {'fields': [], 'legend': curLegend}
        resultat.append(curFieldSet)

    for curProp in Legends:
        curIndex = Unique_Legends.index(curProp[0])
        resultat[curIndex]['fields'].append(curProp[2])

    response['fieldsets'] = resultat

    return response


@view_config(
    route_name=PREFIX + '/id',
    renderer='json',
    request_method='GET',
    permission=routes_permission[PREFIX]['GET'])
def getStation(request):
    session = request.dbsession
    id = request.matchdict['id']
    curSta = session.query(Station).get(id)
    curSta.LoadNowValues()
    # if Form value exists in request --> return data with schema else return
    # only data
    if 'FormName' in request.params:
        # ModuleName = request.params['FormName']
        try:
            DisplayMode = request.params['DisplayMode']
        except:
            DisplayMode = 'display'

        Conf = session.query(FrontModules).filter(
            FrontModules.Name == 'StationForm').first()
        response = curSta.GetDTOWithSchema(Conf, DisplayMode)

        # response['schema']['FK_MonitoredSite']['editable'] = False
        response['data']['fieldActivityId'] = str(
            response['data']['fieldActivityId'])

    else:
        response = curSta.GetFlatObject()

    return response


@view_config(
    route_name=PREFIX + '/id',
    renderer='json',
    request_method='DELETE',
    permission=routes_permission[PREFIX]['DELETE'])
def deleteStation(request):
    session = request.dbsession
    id_ = request.matchdict['id']
    curSta = session.query(Station).get(id_)
    session.delete(curSta)

    return True


@view_config(
    route_name=PREFIX + '/id',
    renderer='json',
    request_method='PUT',
    permission=routes_permission[PREFIX]['PUT'])
def updateStation(request):
    session = request.dbsession
    data = request.json_body
    id = request.matchdict['id']
    if 'creationDate' in data:
        del data['creationDate']
    curSta = session.query(Station).get(id)
    curSta.LoadNowValues()
    try:
        curSta.UpdateFromJson(data)
        session.commit()
        msg = {}
    except IntegrityError as e:
        session.rollback()
        request.response.status_code = 510
        msg = {'existingStation': True}
    return msg


@view_config(
    route_name=PREFIX,
    renderer='json',
    request_method='POST',
    permission=routes_permission[PREFIX]['POST'])
def insertStation(request):
    data = request.json_body
    if not isinstance(data, list):
        return insertOneNewStation(request)
    else:
        return insertListNewStations(request)


def insertOneNewStation(request):
    session = request.dbsession
    data = {}
    for items, value in request.json_body.items():
        data[items] = value

    newSta = Station(
        FK_StationType=data['FK_StationType'],
        creator=request.authenticated_userid['iss'])
    newSta.StationType = session.query(StationType).filter(
        StationType.ID == data['FK_StationType']).first()
    newSta.init_on_load()
    newSta.UpdateFromJson(data)

    try:
        session.add(newSta)
        session.flush()
        msg = {'ID': newSta.ID}
    except IntegrityError as e:
        session.rollback()
        request.response.status_code = 510
        msg = {'existingStation': True}

    return msg


def insertListNewStations(request):
    session = request.dbsession
    data = request.json_body
    data_to_insert = []
    format_dt = '%d/%m/%Y %H:%M'
    dateNow = datetime.now()

    # Rename field and convert date
    # TODO
    for row in data:
        newRow = {}
        newRow['LAT'] = row['latitude']
        newRow['LON'] = row['longitude']
        newRow['ELE'] = row['elevation']
        newRow['precision'] = row['precision']
        newRow['Name'] = row['name']
        newRow['fieldActivityId'] = row['fieldActivity']
        newRow['precision'] = 10  # row['Precision']
        newRow['creationDate'] = dateNow
        newRow['creator'] = request.authenticated_userid['iss']
        newRow['FK_StationType'] = 4
        newRow['id'] = row['id']
        newRow['NbFieldWorker'] = row['NbFieldWorker']
        newRow['StationDate'] = datetime.strptime(
            row['waypointTime'], format_dt)

        if 'fieldActivity' in row:
            newRow['fieldActivityId'] = row['fieldActivity']

        if 'NbFieldWorker' in row:
            newRow['NbFieldWorker'] = row['NbFieldWorker']

        data_to_insert.append(newRow)

    # Load date into pandas DataFrame then round LAT,LON into decimal(5)
    DF_to_check = pd.DataFrame(data_to_insert)
    DF_to_check['LAT'] = DF_to_check['LAT'].round(5)
    DF_to_check['LON'] = DF_to_check['LON'].round(5)
    # DF_to_check['LAT'] = np.round(DF_to_check['LAT'],decimals = 5)
    # DF_to_check['LON'] = np.round(DF_to_check['LON'],decimals = 5)
    # DF_to_check['LAT'] = DF_to_check['LAT'].astype(float)
    # DF_to_check['LON'] = DF_to_check['LON'].astype(float)
    # Get min/max Value to query potential duplicated stations
    maxDate = DF_to_check['StationDate'].max()
    minDate = DF_to_check['StationDate'].min()
    maxLon = DF_to_check['LON'].max()
    minLon = DF_to_check['LON'].min()
    maxLat = DF_to_check['LAT'].max()
    minLat = DF_to_check['LAT'].min()
    # Retrieve potential duplicated stations from Database
    query = select([Station]).where(
        and_(
            Station.StationDate.between(minDate, maxDate),
            Station.LAT.between(minLat, maxLat)
        )).where(Station.LON.between(minLon, maxLon))

    data_to_insert = []
    result_to_check = pd.read_sql_query(query, session.get_bind())
    if result_to_check.shape[0] > 0:
        # IF potential duplicated stations, load them into pandas DataFrame
        result_to_check['LAT'] = result_to_check['LAT'].round(5)
        result_to_check['LON'] = result_to_check['LON'].round(5)

        merge_check = pd.merge(DF_to_check, result_to_check, on=[
                               'LAT', 'LON', 'StationDate'])
        # Get only non existing data to insert
        DF_to_insert = DF_to_check[~DF_to_check['id'].isin(merge_check['id'])]
        DF_to_insert = DF_to_insert.drop(['id'], 1)
        data_to_insert = json.loads(DF_to_insert.to_json(
            orient='records', date_format='iso'))

    else:
        data_to_insert = json.loads(DF_to_check.to_json(
            orient='records', date_format='iso'))

    staListID = []
    nbExc = 0

    if len(data_to_insert) != 0:
        for sta in data_to_insert:
            curSta = Station(FK_StationType=4)
            curSta.init_on_load()
            curDate = datetime.strptime(
                sta['StationDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
            curSta.UpdateFromJson(sta)
            curSta.StationDate = curDate

            try:
                session.add(curSta)
                session.flush()
                session.commit()
                staListID.append(curSta.ID)
            except IntegrityError as e:
                session.rollback()
                nbExc += 1
                pass

        result = staListID

        # Insert FieldWorkers
        if not data[0]['FieldWorkers'] is None or not data[0]['FieldWorkers'] == "":
            list_ = list(map(lambda b: list(map(lambda a: {
                         'FK_Station': a,
                         'FK_FieldWorker': b},
                         result)),
                         data[0]['FieldWorkers']))
            list_ = list(itertools.chain.from_iterable(list_))
            stmt = Station_FieldWorker.__table__.insert().values(list_)
            session.execute(stmt)
    else:
        result = []
    response = {'exist': len(data) - len(data_to_insert) +
                nbExc, 'new': len(data_to_insert) - nbExc}
    return response


@view_config(
    route_name=PREFIX,
    renderer='json',
    request_method='GET',
    permission=routes_permission[PREFIX]['GET'])
def searchStation(request):
    session = request.dbsession

    ''' return data according to filter parameter,
    if "geo" is in request return geojson format '''
    data = request.params.mixed()
    searchInfo = {}
    searchInfo['criteria'] = []
    user = request.authenticated_userid['iss']

    # add filter parameters to retrieve last stations imported : last day of
    # station created by user and without linked observation ####
    def lastImported(obj, searchInfo):
        obj['Operator'] = '='
        obj['Value'] = True
        criteria = [
            {'Column': 'creator',
             'Operator': '=',
             'Value': user
             },
            {'Column': 'FK_StationType',
             'Operator': '=',
             'Value': 4  # => TypeID of GPX station
             }
        ]
        searchInfo['criteria'].extend(criteria)

    if 'criteria' in data:
        data['criteria'] = json.loads(data['criteria'])
        if data['criteria'] != {}:
            searchInfo['criteria'] = [obj for obj in data[
                'criteria'] if obj['Value'] != str(-1)]
            for obj in searchInfo['criteria']:
                if obj['Column'] == 'LastImported':
                    lastImported(obj, searchInfo)

    if 'geo' not in data:
        ModuleType = 'StationGrid'
        searchInfo['order_by'] = json.loads(data['order_by'])
        searchInfo['offset'] = json.loads(data['offset'])
        searchInfo['per_page'] = json.loads(data['per_page'])
        getFW = True
    else:
        searchInfo['order_by'] = []
        ModuleType = 'StationGrid'
        getFW = False
        criteria = [
            {'Column': 'LAT',
             'Operator': 'Is not',
             'Value': None
             },
            {
                'Column': 'LON',
                'Operator': 'Is not',
                'Value': None
            }]
        searchInfo['criteria'].extend(criteria)

    criteria = [
        {'Column': 'creator',
         'Operator': '=',
         'Value': user
         }
    ]
    searchInfo['criteria'].extend(criteria)
        # searchInfo['offset'] = 0

    moduleFront = session.query(FrontModules).filter(
        FrontModules.Name == ModuleType).one()
    listObj = StationList(moduleFront)
    countResult = listObj.count(searchInfo)

    if 'geo' in data:
        geoJson = []
        exceed = True
        if countResult < 50000:
            exceed = False
            dataResult = listObj.GetFlatDataList(searchInfo, getFW)
            for row in dataResult:
                geoJson.append({
                    'type': 'Feature',
                    'properties': {
                        'name': row['Name'],
                        'date': row['StationDate']},
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [row['LAT'], row['LON']]}
                })
        return {'type': 'FeatureCollection',
                'features': geoJson,
                'exceed': exceed}
    else:
        dataResult = listObj.GetFlatDataList(searchInfo, getFW)
        result = [{'total_entries': countResult}]
        result.append(dataResult)
        return result


def updateMonitoredSite(request):
    session = request.dbsession
    data = request.params.mixed()
    curSta = session.query(Station).get(data['id'])

    if data['FK_MonitoredSite'] == '':
        return 'Station is not monitored'
    try:
        newSitePos = MonitoredSitePosition(
            StartDate=curSta.StationDate,
            LAT=curSta.LAT,
            LON=curSta.LON,
            ELE=curSta.ELE,
            Precision=curSta.precision,
            FK_MonitoredSite=curSta.FK_MonitoredSite)

        session.add(newSitePos)
        session.commit()
        return 'Monitored site position was updated'
    except IntegrityError as e:
        session.rollback()

        return 'This location already exists'


@view_config(
    route_name=PREFIX + '/export',
    renderer='json',
    request_method='GET',
    permission=routes_permission[PREFIX]['GET'])
def stations_export(request):
    session = request.dbsession
    data = request.params.mixed()
    searchInfo = {}
    searchInfo['criteria'] = []
    if 'criteria' in data:
        data['criteria'] = json.loads(data['criteria'])
        if data['criteria'] != {}:
            searchInfo['criteria'] = [obj for obj in data[
                'criteria'] if obj['Value'] != str(-1)]

    searchInfo['order_by'] = []
    criteria = [
        {'Column': 'creator',
         'Operator': '=',
         'Value': user
         }
    ]
    searchInfo['criteria'].extend(criteria)
    ModuleType = 'StationGrid'
    moduleFront = session.query(FrontModules).filter(
        FrontModules.Name == ModuleType).one()

    listObj = StationList(moduleFront)
    dataResult = listObj.GetFlatDataList(searchInfo)

    df = pd.DataFrame.from_records(dataResult, columns=dataResult[
                                   0].keys(), coerce_float=True)

    fout = io.BytesIO()
    writer = pd.ExcelWriter(fout)
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    file = fout.getvalue()

    dt = datetime.now().strftime('%d-%m-%Y')
    return Response(
        file,
        content_disposition='attachment; filename=stations_export_'+ dt + '.xlsx',
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
