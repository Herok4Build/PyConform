#!/usr/bin/env python

from pyconform.physarray import PhysArray, UnitsError, DimensionsError
from pyconform.functions import Function, is_constant
from cf_units import Unit
from numpy import diff, empty, mean
import numpy as np

#=========================================================================
# ZonalMeanFunction
#=========================================================================


class ZonalMeanFunction(Function):
    key = 'zonalmean'

    def __init__(self, data):
        super(ZonalMeanFunction, self).__init__(data)
        data_info = data if is_constant(data) else data[None]
        if not isinstance(data_info, PhysArray):
            raise TypeError('mean: Data must be a PhysArray')

    def __getitem__(self, index):
        data = self.arguments[0][index]
        m = mean(data, axis=3)
        return m
        # return mean(data, axis=3)


#=========================================================================
# OclimFunction
#=========================================================================
class OclimFunction(Function):
    key = 'oclim'

    def __init__(self, data):
        super(OclimFunction, self).__init__(data)
        data_info = data if is_constant(data) else data[None]
        if not isinstance(data_info, PhysArray):
            raise TypeError('oclim: Data must be a PhysArray')

    def __getitem__(self, index):
 
        data = self.arguments[0][index]
        new_name = 'oclim({})'.format(data.name)

        if index is None:
            if len(data.dimensions) == 3:
                return PhysArray(np.zeros((0, 0, 0)), dimensions=[data.dimensions[0], data.dimensions[1], data.dimensions[2]], units=data.units)
            elif len(data.dimensions) == 4:
                return PhysArray(np.zeros((0, 0, 0, 0)), units=data.units, dimensions=[data.dimensions[0], data.dimensions[1], data.dimensions[2], data.dimensions[3]])
       
        if len(data.dimensions) == 3:
            a = np.ma.zeros((12,data.data.shape[1],data.data.shape[2]))
        elif len(data.dimensions) == 4:
            a = np.ma.zeros((12,data.data.shape[1],data.data.shape[2],data.data.shape[3]))

        dim_count = len(data.dimensions)
        time = data.data.shape[0]
        dataD = data.data

        for i in range(12):
            a[i,...] = np.ma.mean(dataD[i::12,...],axis=0)  

        a[a>=1e+16] = 1e+20
        a = np.ma.masked_values(a, 1e+20)

        if dim_count == 3:
            a = PhysArray(a, name = new_name,  units=data.units, dimensions=[data.dimensions[0], data.dimensions[1], data.dimensions[2]])
        elif dim_count == 4:
            a = PhysArray(a, name = new_name,  units=data.units, dimensions=[data.dimensions[0], data.dimensions[1], data.dimensions[2], data.dimensions[3]])

        return a


#=========================================================================
# oclim_timeFunction
#=========================================================================


class oclim_timeFunction(Function):
    key = 'oclim_time'

    def __init__(self, time_bnds):
        super(oclim_timeFunction, self).__init__(time_bnds)

    def __getitem__(self, index):
        p_time_bnds = self.arguments[0][index]

        if index is None:
            return PhysArray(np.zeros((0)), dimensions=[p_time_bnds.dimensions[0]], units=p_time_bnds.units, calendar='noleap')

        time_bnds = p_time_bnds.data

        b = np.zeros((12))
        for i in range(12):
            b[i] = (time_bnds[i][0]+time_bnds[i][1])/2        

        new_name = 'oclim_time({})'.format(p_time_bnds.name)

        return PhysArray(b, name = new_name, dimensions=[p_time_bnds.dimensions[0]], units=p_time_bnds.units, calendar='noleap')


#=========================================================================
# oclim_timebndsFunction
#=========================================================================


class oclim_timebndsFunction(Function):
    key = 'oclim_timebnds'

    def __init__(self, time, bdim='bnds'):
        super(oclim_timebndsFunction, self).__init__(time, bdim='d2')

    def __getitem__(self, index):
        p_time = self.arguments[0][index]
        bdim = self.keywords['bdim']

        bnds = PhysArray([1, 1], dimensions=(bdim,))

        if index is None:
            return PhysArray(np.zeros((12,2)), dimensions=[p_time.dimensions[0], bnds.dimensions[0]], units=p_time.units, calendar='noleap')

        b = np.zeros((12,2))
        time = p_time.data

        monLens = [31.0, 28.0, 31.0, 30.0, 31.0,
                   30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]

        for i in range(11,-1,-1):
            b[i][0] = time[i] - monLens[i]
            b[i][1] = time[-(12-i)]
        new_name = 'oclim_timebnds({})'.format(p_time.name)

        return PhysArray(b, name = new_name, dimensions=[p_time.dimensions[0], bnds.dimensions[0]], units=p_time.units, calendar='noleap')


#=========================================================================
# monthtoyear_noleapFunction
#=========================================================================
class monthtoyear_noleapFunction(Function):
    key = 'monthtoyear_noleap'

    def __init__(self, data):
        super(monthtoyear_noleapFunction, self).__init__(data)
        data_info = data if is_constant(data) else data[None]
        if not isinstance(data_info, PhysArray):
            raise TypeError('monthtoyear_noleap: Data must be a PhysArray')

    def __getitem__(self, index):

        data = self.arguments[0][index]
        new_name = 'monthtoyear_noleap({})'.format(data.name)

        if index is None:
            if len(data.dimensions) == 3:
                return PhysArray(np.zeros((0, 0, 0)), dimensions=[data.dimensions[0], data.dimensions[1], data.dimensions[2]], units=data.units)
            elif len(data.dimensions) == 4:
                return PhysArray(np.zeros((0, 0, 0, 0)), units=data.units, dimensions=[data.dimensions[0], data.dimensions[1], data.dimensions[2], data.dimensions[3]])

        if len(data.dimensions) == 3:
            a = np.ma.zeros((data.data.shape[0]/12,data.data.shape[1],data.data.shape[2]))
        elif len(data.dimensions) == 4:
            a = np.ma.zeros((data.data.shape[0]/12,data.data.shape[1],data.data.shape[2],data.data.shape[3]))

        dim_count = len(data.dimensions)
        time = data.data.shape[0]
        dataD = data.data

        for i in range(time/12):
            start = i*12
            end = (i*12)+11
            a[i,...] = np.ma.mean(dataD[start:end,...],axis=0)

        a[a>=1e+16] = 1e+20
        a = np.ma.masked_values(a, 1e+20)

        if dim_count == 3:
            a1 = PhysArray(a, name = new_name,  units=data.units, dimensions=[data.dimensions[0], data.dimensions[1], data.dimensions[2]])
        elif dim_count == 4:
            a1 = PhysArray(a, name = new_name,  units=data.units, dimensions=[data.dimensions[0], data.dimensions[1], data.dimensions[2], data.dimensions[3]])
      
        return a1


#=========================================================================
# monthtoyear_timeFunction
#=========================================================================


class monthtoyear_noleap_timeFunction(Function):
    key = 'monthtoyear_noleap_time'

    def __init__(self, time_bnds):
        super(monthtoyear_noleap_timeFunction, self).__init__(time_bnds)

    def __getitem__(self, index):
        p_time_bnds = self.arguments[0][index]

        if index is None:
            return PhysArray(np.zeros((0)), dimensions=[p_time_bnds.dimensions[0]], units=p_time_bnds.units, calendar='noleap')

        time_bnds = p_time_bnds.data

        b = np.zeros((time_bnds.shape[0]/12))
        time = time_bnds.shape[0]
        for i in range(time/12):
            start = i*12
            end = (i*12)+11
            b[i] = (time_bnds[start][0]+time_bnds[end][1])/2

        new_name = 'monthtoyear_noleap_time({})'.format(p_time_bnds.name)

        return PhysArray(b, name = new_name, dimensions=[p_time_bnds.dimensions[0]], units=p_time_bnds.units, calendar='noleap')


#=========================================================================
# monthtoyear_timebndsFunction
#=========================================================================


class monthtoyear_noleap_timebndsFunction(Function):
    key = 'monthtoyear_noleap_timebnds'

    def __init__(self, time, bdim='bnds'):
        super(monthtoyear_noleap_timebndsFunction, self).__init__(time, bdim='d2')

    def __getitem__(self, index):
        p_time = self.arguments[0][index]
        bdim = self.keywords['bdim']

        bnds = PhysArray([1, 1], dimensions=(bdim,))

        if index is None:
            return PhysArray(np.zeros((12,2)), dimensions=[p_time.dimensions[0], bnds.dimensions[0]], units=p_time.units, calendar='noleap')

        time = p_time.data
        b = np.zeros((time.shape[0]/12,2))

        for i in range(len(time)/12):
            b[i][0] = time[i*12]
            b[i][1] = time[(i*12)+11]
        new_name = 'monthtoyear_noleap_timebnds({})'.format(p_time.name)

        return PhysArray(b, name = new_name, dimensions=[p_time.dimensions[0], bnds.dimensions[0]], units=p_time.units, calendar='noleap')


#=========================================================================
# BoundsFunction
#=========================================================================
class BoundsFunction(Function):
    key = 'bounds'

    def __init__(self, data, bdim='bnds', location=1, endpoints=1, idata=None):
        super(BoundsFunction, self).__init__(data, bdim=bdim,
                                             location=location, endpoints=endpoints, idata=idata)
        data_info = data if is_constant(data) else data[None]
        if not isinstance(data_info, PhysArray):
            raise TypeError('bounds: data must be a PhysArray')
        if not isinstance(bdim, basestring):
            raise TypeError('bounds: bounds dimension name must be a string')
        if location not in [0, 1, 2]:
            raise ValueError('bounds: location must be 0, 1, or 2')
        if len(data_info.dimensions) != 1:
            raise DimensionsError('bounds: data can only be 1D')
        self._mod_end = bool(endpoints)
#        self.add_sumlike_dimensions(data_info.dimensions[0])
        if idata is None:
            self._compute_idata = True
        else:
            self._compute_idata = False
            idata_info = idata if is_constant(idata) else idata[None]
            if not isinstance(idata_info, PhysArray):
                raise TypeError('bounds: interface-data must be a PhysArray')
            if len(idata_info.dimensions) != 1:
                raise DimensionsError('bounds: interface-data can only be 1D')
#            self.add_sumlike_dimensions(idata_info.dimensions[0])

    def __getitem__(self, index):
        data = self.arguments[0][index]
        bdim = self.keywords['bdim']
        location = self.keywords['location']

        bnds = PhysArray([1, 1], dimensions=(bdim,))
        new_data = PhysArray(data * bnds, name='bounds({})'.format(data.name), units=data.units)
        if index is None:
            return new_data

        if self._compute_idata:
            dx = diff(data.data)
            if location == 0:
                new_data[:-1, 1] = data.data[:-1] + dx
                if self._mod_end:
                    new_data[-1, 1] = data.data[-1] + dx[-1]
            elif location == 1:
                hdx = 0.5 * dx
                new_data[1:, 0] = data.data[1:] - hdx
                new_data[:-1, 1] = data.data[:-1] + hdx
                if self._mod_end:
                    new_data[0, 0] = data.data[0] - hdx[0]
                    new_data[-1, 1] = data.data[-1] + hdx[-1]
            elif location == 2:
                new_data[1:, 0] = data.data[1:] - dx
                if self._mod_end:
                    new_data[0, 0] = data.data[0] - dx[0]
            return new_data

        else:
            ddim = data.dimensions[0]
            dslice = index[ddim] if ddim in index else slice(None)
            islice = slice(None, None, dslice.step)
            idata = self.keywords['idata'][islice]

            ifc_len = len(data) + 1
            ifc_data = empty(ifc_len, dtype=data.dtype)
            if len(idata) == ifc_len:
                ifc_data[:] = idata.data[:]
            elif len(idata) == ifc_len - 2:
                ifc_data[1:-1] = idata.data[:]
                if location == 0:
                    ifc_data[0] = data.data[0]
                    ifc_data[-1] = 2 * data.data[-1] - data.data[-2]
                elif location == 1:
                    ifc_data[0] = 2 * data.data[0] - idata.data[0]
                    ifc_data[-1] = 2 * data.data[-1] - idata.data[-1]
                else:
                    ifc_data[0] = 2 * data.data[0] - data.data[1]
                    ifc_data[-1] = data.data[-1]
            else:
                raise ValueError('bounds: interface-data length is {} but should be {} or '
                                 '{}'.format(len(idata), ifc_len, ifc_len - 2))

            new_data[:, 0] = ifc_data[:-1]
            new_data[:, 1] = ifc_data[1:]

        return new_data

#=========================================================================
# AgeofAirFunction
#=========================================================================


class AgeofAirFunction(Function):
    key = 'ageofair'

    def __init__(self, spc_zm, date, time, lat, lev):
        super(AgeofAirFunction, self).__init__(spc_zm, date, time, lat, lev)

    def __getitem__(self, index):
        p_spc_zm = self.arguments[0][index]
        p_date = self.arguments[1][index]
        p_time = self.arguments[2][index]
        p_lat = self.arguments[3][index]
        p_lev = self.arguments[4][index]

        if index is None:
            return PhysArray(np.zeros((0, 0, 0)), dimensions=[p_time.dimensions[0], p_lev.dimensions[0], p_lat.dimensions[0]])

        spc_zm = p_spc_zm.data
        date = p_date.data
        time = p_time.data
        lat = p_lat.data
        lev = p_lev.data

        a = np.zeros((len(time), len(lev), len(lat)))

        # Unpack month and year.  Adjust to compensate for the output
        # convention in h0 files
        year = date / 10000
        month = (date / 100 % 100)
        day = date - 10000 * year - 100 * month

        month = month - 1
        for m in range(len(month)):
            if month[m] == 12:
                year[m] = year[m] - 1
                month[m] = 0

        timeyr = year + (month - 0.5) / 12.

        spc_ref = spc_zm[:, 0, 0]
        for iy in range(len(lat)):
            for iz in range(len(lev)):
                spc_local = spc_zm[:, iz, iy]
                time0 = np.interp(spc_local, spc_ref, timeyr)
                a[:, iz, iy] = timeyr - time0

        new_name = 'ageofair({}{}{}{}{})'.format(
            p_spc_zm.name, p_date.name, p_time.name, p_lat.name, p_lev.name)

        return PhysArray(a, name=new_name, units="yr")


#=========================================================================
# yeartomonth_dataFunction
#=========================================================================
class YeartoMonth_dataFunction(Function):
    key = 'yeartomonth_data'

    def __init__(self, data, time, lat, lon):
        super(YeartoMonth_dataFunction, self).__init__(data, time, lat, lon)

    def __getitem__(self, index):
        p_data = self.arguments[0][index]
        p_time = self.arguments[1][index]
        p_lat = self.arguments[2][index]
        p_lon = self.arguments[3][index]

        if index is None:
            return PhysArray(np.zeros((0, 0, 0)), dimensions=[p_time.dimensions[0], p_lat.dimensions[0], p_lon.dimensions[0]])

        data = p_data.data
        time = p_time.data
        lat = p_lat.data
        lon = p_lon.data
       
        if time[0] == 0:
            a = np.ma.zeros(((len(time)-1)*12,len(lat),len(lon)))
        else:
            a = np.ma.zeros((len(time)*12,len(lat),len(lon)))

        k=0
        for i in range(len(time)):
            if time[i] != 0:
                for j in range(12):
                    a[((k*12)+j),:,:] = data[i,:,:]
                k+=1

        a[a>=1e+16] = 1e+20
        a = np.ma.masked_values(a, 1e+20)
        new_name = 'yeartomonth_data({}{}{}{})'.format(p_data.name, p_time.name, p_lat.name, p_lon.name)

        return PhysArray(a, name = new_name, dimensions=[p_time.dimensions[0],p_lat.dimensions[0],p_lon.dimensions[0]], units=p_data.units)                 


#===================================================================================================
# yeartomonth_data3DFunction
#===================================================================================================
class YeartoMonth_data3DFunction(Function):
    key = 'yeartomonth_data3D'

    def __init__(self, data, time, lat, lon, v):
        super(YeartoMonth_data3DFunction, self).__init__(data, time, lat, lon, v)

    def __getitem__(self, index):
        p_data = self.arguments[0][index]
        p_time = self.arguments[1][index]
        p_lat = self.arguments[2][index]
        p_lon = self.arguments[3][index]
        p_v = self.arguments[4][index]

        if index is None:
            return PhysArray(np.zeros((0,0,0,0)), dimensions=[p_time.dimensions[0],p_v.dimensions[0],p_lat.dimensions[0],p_lon.dimensions[0]])

        data = p_data.data
        time = p_time.data
        lat = p_lat.data
        lon = p_lon.data
        v = p_v.data

        if time[0] == 0:
            a = np.ma.zeros(((len(time)-1)*12,len(v),len(lat),len(lon)))
        else:
            a = np.ma.zeros((len(time)*12,len(v),len(lat),len(lon)))

        k=0
        for i in range(len(time)):
            if time[i] != 0:
                for j in range(12):
                    a[((k*12)+j),:,:,:] = data[i,:,:,:]
                k+=1

        a[a>=1e+16] = 1e+20
        a = np.ma.masked_values(a, 1e+20)
        new_name = 'yeartomonth_data({}{}{}{}{})'.format(p_data.name, p_time.name, p_lat.name, p_lon.name, p_v.name)

        return PhysArray(a, name = new_name, dimensions=[p_time.dimensions[0],p_v.dimensions[0],p_lat.dimensions[0],p_lon.dimensions[0]], units=p_data.units)

#=========================================================================
# yeartomonth_timeFunction
#=========================================================================


class YeartoMonth_timeFunction(Function):
    key = 'yeartomonth_time'

    def __init__(self, time):
        super(YeartoMonth_timeFunction, self).__init__(time)

    def __getitem__(self, index):
        p_time = self.arguments[0][index]

        if index is None:
            return PhysArray(np.zeros((0)), dimensions=[p_time.dimensions[0]], units=p_time.units, calendar='noleap')

        time = p_time.data
        monLens = [31.0, 28.0, 31.0, 30.0, 31.0,
                   30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]

        a = np.zeros((len(time)*12))

        k=0
        for i in range(len(time)):
            prev = 0
            if time[i] != 0:
                for j in range(12):
                        a[((k*12)+j)] = float((time[i]-365)+prev+float(monLens[j]/2.0))
                        prev += monLens[j]
                k+=1

        if a[-1] == 0 and not np.all(a==0):
            b = np.resize(a,((len(time)-1)*12))
        else:
            b = a
        new_name = 'yeartomonth_time({})'.format(p_time.name)

        return PhysArray(b, name = new_name, dimensions=[p_time.dimensions[0]], units=p_time.units, calendar='noleap')


#=========================================================================
# POP_bottom_layerFunction
#=========================================================================
class POP_bottom_layerFunction(Function):
    key = 'POP_bottom_layer'

    def __init__(self, KMT, data):
        super(POP_bottom_layerFunction, self).__init__(KMT, data)

    def __getitem__(self, index):
        p_KMT = self.arguments[0][index]
        p_data = self.arguments[1][index]

        if index is None:
            return PhysArray(np.zeros((0, 0, 0)), dimensions=[p_data.dimensions[0], p_data.dimensions[2], p_data.dimensions[3]])

        data = p_data.data
        KMT = p_KMT.data

        a = np.zeros((p_data.shape[0], p_data.shape[2], p_data.shape[3]))

        for j in range(KMT.shape[0]):
            for i in range(KMT.shape[1]):
                a[:, j, i] = data[:, KMT[j, i] - 1, j, i]

        new_name = 'POP_bottom_layer({}{})'.format(p_KMT.name, p_data.name)

        return PhysArray(a, name=new_name, units=p_data.units)


#=========================================================================
# diff_axis1_ind0bczero_4dFunction
#=========================================================================
class diff_axis1_ind0bczero_4dFunction(Function):
    key = 'diff_axis1_ind0bczero_4d'

    def __init__(self, KMT, data):
        super(diff_axis1_ind0bczero_4dFunction, self).__init__(KMT, data)
        data_info = data if is_constant(data) else data[None]
        if not isinstance(data_info, PhysArray):
            raise TypeError('diff_axis1_ind0bczero_4d: data must be a PhysArray')
        if len(data_info.dimensions) != 4:
            raise DimensionsError('diff_axis1_ind0bczero_4d: data can only be 4D')

    def __getitem__(self, index):
        p_KMT = self.arguments[0][index]
        p_data = self.arguments[1][index]

        if index is None:
            a = np.zeros((0, 0, 0, 0))
            fv = 1e+20
        else:
            KMT = p_KMT.data
            data = p_data.data

            a = np.empty((p_data.shape))
            a[:, 0, :, :] = data[:, 0, :, :]
            a[:, 1:, :, :] = np.diff(data, axis=1)

            #fv = data.fill_value
            fv = 1e+20 
            for t in range(p_data.shape[0]):
                for k in range(p_data.shape[1]):
                    a[t, k, :, :] = np.where(k < KMT, a[t, k, :, :], fv)

        ma_a = np.ma.masked_values(a, fv)
        new_name = '{}({}{})'.format(self.key, p_KMT.name, p_data.name)
        new_units = p_data.units
        new_dims = p_data.dimensions
        return PhysArray(ma_a, name=new_name, units=new_units, dimensions=new_dims)


#=========================================================================
# rsdoabsorbFunction
#=========================================================================
class rsdoabsorbFunction(Function):
    key = 'rsdoabsorb'

    def __init__(self, KMT, QSW_3D):
        super(rsdoabsorbFunction, self).__init__(KMT, QSW_3D)
        QSW_3D_info = QSW_3D if is_constant(QSW_3D) else QSW_3D[None]
        if not isinstance(QSW_3D_info, PhysArray):
            raise TypeError('rsdoabsorb: QSW_3D must be a PhysArray')
        if len(QSW_3D_info.dimensions) != 4:
            raise DimensionsError('rsdoabsorb: QSW_3D can only be 4D')

    def __getitem__(self, index):
        p_KMT = self.arguments[0][index]
        p_QSW_3D = self.arguments[1][index]

        if index is None:
            a = np.zeros((0, 0, 0, 0))
            fv = 1e+20
        else:
            KMT = p_KMT.data
            QSW_3D = p_QSW_3D.data

            a = np.empty((p_QSW_3D.shape))

            nlev = p_QSW_3D.shape[1]
            #fv = QSW_3D.fill_value
            fv = 1e+20
            for t in range(p_QSW_3D.shape[0]):
                for k in range(p_QSW_3D.shape[1]):
                    if k < nlev-1:
                        a[t, k, :, :] = np.where(
                            k < KMT-1, QSW_3D[t, k, :, :] - QSW_3D[t, k+1, :, :],
                            QSW_3D[t, k, :, :])
                    else:
                        a[t, k, :, :] = QSW_3D[t, k, :, :]
                    a[t, k, :, :] = np.where(k < KMT, a[t, k, :, :], fv)

        ma_a = np.ma.masked_values(a, fv)
        new_name = '{}({}{})'.format(self.key, p_KMT.name, p_QSW_3D.name)
        new_units = p_QSW_3D.units
        new_dims = p_QSW_3D.dimensions
        return PhysArray(ma_a, name=new_name, units=new_units, dimensions=new_dims)


#=========================================================================
# POP_surf_meanFunction
#=========================================================================
class POP_surf_meanFunction(Function):
    key = 'POP_surf_mean'

    def __init__(self, KMT, TAREA, FIELD):
        super(POP_surf_meanFunction, self).__init__(KMT, TAREA, FIELD)
        FIELD_info = FIELD if is_constant(FIELD) else FIELD[None]
        if not isinstance(FIELD_info, PhysArray):
            raise TypeError('POP_surf_mean: FIELD must be a PhysArray')
        if len(FIELD_info.dimensions) != 3:
            raise DimensionsError('POP_surf_mean: FIELD can only be 3D')

    def __getitem__(self, index):
        p_KMT = self.arguments[0][index]
        p_TAREA = self.arguments[1][index]
        p_FIELD = self.arguments[2][index]

        if index is None:
            return PhysArray(np.zeros((0,)), dimensions=[p_FIELD.dimensions[0]])

        KMT = p_KMT.data
        TAREA = p_TAREA.data
        FIELD = p_FIELD.data

        a = np.empty((p_FIELD.shape[0],))
        for t in range(p_FIELD.shape[0]):
            a[t] = np.sum(np.where(KMT > 0, TAREA * FIELD[t, :, :], 0.0))
        denom = np.sum(np.where(KMT > 0, TAREA, 0.0))
        a[:] *= 1.0 / denom

        new_name = '{}({}{}{})'.format(self.key, p_KMT.name, p_TAREA.name, p_FIELD.name)
        new_units = p_FIELD.units
        new_dims = [p_FIELD.dimensions[0]]
        return PhysArray(a, name=new_name, units=new_units, dimensions=new_dims)


#=========================================================================
# POP_3D_meanFunction
#=========================================================================
class POP_3D_meanFunction(Function):
    key = 'POP_3D_mean'

    def __init__(self, KMT, dz, TAREA, FIELD):
        super(POP_3D_meanFunction, self).__init__(KMT, dz, TAREA, FIELD)
        FIELD_info = FIELD if is_constant(FIELD) else FIELD[None]
        if not isinstance(FIELD_info, PhysArray):
            raise TypeError('POP_3D_mean: FIELD must be a PhysArray')
        if len(FIELD_info.dimensions) != 4:
            raise DimensionsError('POP_3D_mean: FIELD can only be 4D')

    def __getitem__(self, index):
        p_KMT = self.arguments[0][index]
        p_dz = self.arguments[1][index]
        p_TAREA = self.arguments[2][index]
        p_FIELD = self.arguments[3][index]

        if index is None:
            return PhysArray(np.zeros((0,)), dimensions=[p_FIELD.dimensions[0]])

        KMT = p_KMT.data
        dz = p_dz.data
        TAREA = p_TAREA.data
        FIELD = p_FIELD.data

        a = np.empty((p_FIELD.shape[0],))
        for t in range(p_FIELD.shape[0]):
            a[t] = 0.0
            for k in range(p_FIELD.shape[1]):
                a[t] += dz[k] * np.sum(np.where(k < KMT, TAREA * FIELD[t, k, :, :], 0.0))
        denom = 0.0
        for k in range(p_FIELD.shape[1]):
            denom += dz[k] * np.sum(np.where(k < KMT, TAREA, 0.0))
        a[:] *= 1.0 / denom

        new_name = '{}({}{}{}{})'.format(self.key, p_KMT.name, p_dz.name, p_TAREA.name, p_FIELD.name)
        new_units = p_FIELD.units
        new_dims = [p_FIELD.dimensions[0]]
        return PhysArray(a, name=new_name, units=new_units, dimensions=new_dims)



#=========================================================================
# sftofFunction
#=========================================================================
class sftofFunction(Function):
    key = 'sftof'

    def __init__(self, KMT):
        super(sftofFunction, self).__init__(KMT)

    def __getitem__(self, index):
        p_KMT = self.arguments[0][index]

        if index is None:
            return PhysArray(np.zeros((0, 0)), dimensions=[p_KMT.dimensions[0], p_KMT.dimensions[1]])

        KMT = p_KMT.data

        a = np.zeros((KMT.shape[0], KMT.shape[1]))

        for j in range(KMT.shape[0]):
            for i in range(KMT.shape[1]):
                if KMT[j, i] > 0:
                    a[j, i] = 1

        new_name = 'sftof({})'.format(p_KMT.name)

        return PhysArray(a, name=new_name, dimensions=[p_KMT.dimensions[0], p_KMT.dimensions[1]], units=p_KMT.units)


#=========================================================================
# POP_bottom_layer_multFunction
#=========================================================================
class POP_bottom_layer_multaddFunction(Function):
    key = 'POP_bottom_layer_multadd'

    def __init__(self, KMT, data1, data2):
        super(POP_bottom_layer_multaddFunction,
              self).__init__(KMT, data1, data2)

    def __getitem__(self, index):
        p_KMT = self.arguments[0][index]
        p_data1 = self.arguments[1][index]
        p_data2 = self.arguments[2][index]

        data1 = p_data1.data
        data2 = p_data2.data
        KMT = p_KMT.data

        a1 = np.zeros((p_data2.shape[0], p_data2.shape[2], p_data2.shape[3]))
        a2 = np.zeros((p_data2.shape[0]))

        for t in range(p_data2.shape[0]):
            for j in range(KMT.shape[0]):
                for i in range(KMT.shape[1]):
                    k = KMT[j, i] - 1
                    if data2[t, k, j, i] < 1e+16:
                        a1[t, j, i] = data1[k] * data2[t, k, j, i]
                        # print a1[t,j,i],data1[k],data2[t,k,j,i]
        for t in range(p_data2.shape[0]):
            a2[t] = np.ma.sum(a1[t, :, :])
            # print a2[t]

        new_name = 'POP_bottom_layer_multadd({}{}{})'.format(
            p_KMT.name, p_data1.name, p_data2.name)
        new_units = p_data1.units * p_data2.units
        return PhysArray(a2, name=new_name, dimensions=[p_data2.dimensions[0]], units=new_units)

#=========================================================================
# POP_layer_sum_multFunction
#=========================================================================
class POP_layer_sum_multFunction(Function):
    key = 'POP_layer_sum_mult'

    def __init__(self, KMT, data1, data2):
        super(POP_layer_sum_multFunction,
              self).__init__(KMT, data1, data2)

    def __getitem__(self, index):
        p_KMT = self.arguments[0][index]
        p_data1 = self.arguments[1][index]
        p_data2 = self.arguments[2][index]

        data1 = p_data1.data
        data2 = p_data2.data
        KMT = p_KMT.data

        a1 = np.zeros((p_data2.shape[0], p_data2.shape[2], p_data2.shape[3]))

        #fv = data2.fill_value
        fv = 1e+20

        for t in range(p_data2.shape[0]):
            for j in range(KMT.shape[0]):
                for i in range(KMT.shape[1]):
                    if KMT[j, i] > 0:
                        a1[t, j, i] = 0.0
                        for k in range(min(KMT[j, i], p_data2.shape[1])):
                            a1[t, j, i] += data1[k] * data2[t, k, j, i]
                    else:
                        a1[t, j, i] = fv

        ma_a1 = np.ma.masked_values(a1, fv)
        new_name = 'POP_layer_sum_mult({}{}{})'.format(
            p_KMT.name, p_data1.name, p_data2.name)
        new_units = p_data1.units * p_data2.units
        return PhysArray(ma_a1, name=new_name, dimensions=[p_data2.dimensions[0], p_data2.dimensions[2], p_data2.dimensions[3]], units=new_units)

#=========================================================================
# masked_invalidFunction
#=========================================================================
class masked_invalidFunction(Function):
    key = 'masked_invalid'

    def __init__(self, data):
        super(masked_invalidFunction, self).__init__(data)

    def __getitem__(self, index):
        p_data = self.arguments[0][index]

        if index is None:
            return PhysArray(np.zeros((0, 0, 0)), dimensions=[p_data.dimensions[0], p_data.dimensions[1], p_data.dimensions[2]])

        data = p_data.data

        a = np.ma.masked_invalid(data)

        new_name = 'masked_invalid({})'.format(p_data.name)

        return PhysArray(a, name=new_name, units=p_data.units)


#=========================================================================
# hemisphereFunction
#=========================================================================
class hemisphereFunction(Function):
    key = 'hemisphere'

    def __init__(self, data, dim='dim', dr='dr'):
        super(hemisphereFunction, self).__init__(data, dim=dim, dr=dr)

    def __getitem__(self, index):
        p_data = self.arguments[0][index]
        dim = self.keywords['dim']
        dr = self.keywords['dr']

        data = p_data.data

        a = None

        # dim0?
        if dim in p_data.dimensions[0]:
            if ">" in dr:
                return p_data[(data.shape[0] / 2):data.shape[0], :, :]
            elif "<" in dr:
                return p_data[0:(data.shape[0] / 2), :, :]
        # dim1?
        if dim in p_data.dimensions[1]:
            if ">" in dr:
                return p_data[:, (data.shape[1] / 2):data.shape[1], :]
            elif "<" in dr:
                return p_data[:, 0:(data.shape[1] / 2), :]
        # dim2?
        if dim in p_data.dimensions[2]:
            if ">" in dr:
                return p_data[:, :, (data.shape[2] / 2):data.shape[2]]
            elif "<" in dr:
                return p_data[:, :, 0:(data.shape[2] / 2)]


#=========================================================================
# cice_whereFunction
#=========================================================================
class cice_whereFunction(Function):
    key = 'cice_where'

    # np.where(x < 5, x, -1)

    def __init__(self, a1, condition, a2, var, value):
        super(cice_whereFunction, self).__init__(a1, condition, a2, var, value)

    def __getitem__(self, index):
        a1 = self.arguments[0][index]
        condition = self.arguments[1]
        a2 = self.arguments[2]
        var = self.arguments[3][index]
        value = self.arguments[4]

        if index is None:
            return PhysArray(a1.data, dimensions=[a1.dimensions[0], a1.dimensions[1], a1.dimensions[2]])

        a = np.ma.zeros(a1.shape)
        for t in range(a1.data.shape[0]):
            if '>=' in condition:
                a[t, :, :] = np.ma.where(a1[t, :, :] >= a2, var, value)
            elif '<=' in condition:
                a[t, :, :] = np.ma.where(a1[t, :, :] <= a2, var, value)
            elif '==' in condition:
                a[t, :, :] = np.ma.where(a1[t, :, :] == a2, var, value)
            elif '<' in condition:
                a[t, :, :] = np.ma.where(a1[t, :, :] < a2, var, value)
            elif '>' in condition:
                a[t, :, :] = np.ma.where(a1[t, :, :] > a2, var, value)

        new_name = 'cice_where()'.format()
        return PhysArray(a, name=new_name, dimensions=[a1.dimensions[0], a1.dimensions[1], a1.dimensions[2]], units=var.units)


#=========================================================================
# cice_regions
#=========================================================================
class cice_regionsFunction(Function):
    key = 'cice_regions'

    def __init__(self, p_aice, p_uvel, p_vvel, p_HTE, p_HTN, p_siline, multiple):
        super(cice_regionsFunction, self).__init__(
            p_aice, p_uvel, p_vvel, p_HTE, p_HTN, p_siline, multiple)

    def __getitem__(self, index):
        p_aice = self.arguments[0][index]
        p_uvel = self.arguments[1][index]
        p_vvel = self.arguments[2][index]
        p_HTE = self.arguments[3][index]
        p_HTN = self.arguments[4][index]
        p_siline = self.arguments[5][index]
        multiple = self.arguments[6]

        aice = p_aice.data
        uvel = p_uvel.data
        vvel = p_vvel.data
        HTE = p_HTE.data
        HTN = p_HTN.data
        siline = p_siline.data
        a = np.ma.zeros((aice.shape[0], siline.shape[0]))

        uvel[uvel >= 1e+16] = 0.0
        vvel[vvel >= 1e+16] = 0.0  
 
        for t in range(aice.shape[0]):
            # 1
            i = 92
            for j in range(370, 381):
                if aice[t, j, i] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i
                elif aice[t, j, i + 1] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i + 1
                else:
                    a[t, 0] += 0.5 * (aice[t, j, i] + aice[t, j, i + 1]) * 0.5 * (
                        HTE[j, i] * uvel[t, j, i] + HTE[j, i] * uvel[t, j - 1, i])
            # 2
            i = 214
            for j in range(375, 377):
                if aice[t, j, i] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i
                elif aice[t, j, i + 1] >= 1e+16: 
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i + 1
                elif aice[t, j + 1, i] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j + 1, i
                else:
                    a[t, 1] += 0.5 * (aice[t, j, i] + aice[t, j, i + 1]) * 0.5 * (HTE[j, i] * uvel[t, j, i] + HTE[j, i] * uvel[t, j - 1, i]) + 0.5 * (
                        aice[t, j, i] + aice[t, j + 1, i]) * 0.5 * (HTN[j, i] * vvel[t, j, i] + HTN[j, i] * vvel[t, j, i - 1])
            j = 366
            for i in range(240, 244):
                if aice[t, j, i] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i
                elif aice[t, j, i + 1] >= 1e+16: 
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i + 1
                elif aice[t, j + 1, i] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j + 1, i
                else:
                    a[t, 1] += 0.5 * (aice[t, j, i] + aice[t, j, i + 1]) * 0.5 * (HTE[j, i] * uvel[t, j, i] + HTE[j, i] * uvel[t, j - 1, i]) + 0.5 * (
                        aice[t, j, i] + aice[t, j + 1, i]) * 0.5 * (HTN[j, i] * vvel[t, j, i] + HTN[j, i] * vvel[t, j, i - 1])
            # 3
            i = 85
            for j in range(344, 366):
                if aice[t, j, i] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i
                elif aice[t, j, i + 1] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i + 1
                else:
                    a[t, 2] += 0.5 * (aice[t, j, i] + aice[t, j, i + 1]) * 0.5 * (
                        HTE[j, i] * uvel[t, j, i] + HTE[j, i] * uvel[t, j - 1, i])
            # 4
            j = 333
            for i in range(198, 201):
                if aice[t, j, i] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j, i
                elif aice[t, j + 1, i] >= 1e+16:
                    print "CICE aice WARNING: this point should not contain a missing value ",t, j + 1, i
                else:
                    a[t, 3] += 0.5 * (aice[t, j, i] + aice[t, j + 1, i]) * 0.5 * (
                        HTN[j, i] * vvel[t, j, i] + HTN[j, i] * vvel[t, j, i - 1])

        a = a * multiple

        new_name = 'cice_regions()'.format()
        return PhysArray(a, name=new_name, dimensions=[p_aice.dimensions[0], p_siline.dimensions[0]], units=p_uvel.units)


#=========================================================================
# burntFractionFunction
#=========================================================================
class burntFractionFunction(Function):
    key = 'burntFraction'

    def __init__(self, data):
        super(burntFractionFunction, self).__init__(data)

    def __getitem__(self, index):
        p_data = self.arguments[0][index]

        if index is None:
            return PhysArray(np.zeros((0, 0, 0)), dimensions=[p_data.dimensions[0], p_data.dimensions[1], p_data.dimensions[2]])

        data = p_data.data

        ml = [31.0, 28.0, 31.0, 30.0, 31.0,
                   30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0] 

        a = np.ma.zeros((data.shape[0], data.shape[1], data.shape[2]))

        i = 0
        for t in range(0,data.shape[0]):
            for x in range(0,data.shape[1]):
                for y in range(0,data.shape[2]):
                    if data[t,x,y]<1e+16:
                        a[t,x,y] = data[t,x,y]*ml[i]*86400*100
                    else:
                        a[t,x,y] = 1e+20
            i+=1
            if i==12:
                i=1
        a[a >= 1e+16] = 1e+20
        new_name = 'burntFraction({})'.format(p_data.name)

        return PhysArray(a, name=new_name, units=p_data.units)


#=========================================================================
# reduce_luFunction
#=========================================================================
class reduce_luFunction(Function):
    key = 'reduce_lu'

    # np.where(x < 5, x, -1)

    def __init__(self, p_data, p_lu):
        super(reduce_luFunction, self).__init__(p_data, p_lu)

    def __getitem__(self, index):
        p_data = self.arguments[0][index]
        p_lu = self.arguments[1][index]

        # if index is None:
        # return PhysArray(p_data.data,
        # dimensions=[p_data.dimensions[0],p_lu.dimensions[0],p_data.dimensions[2],p_data.dimensions[3]])

        data = p_data.data
        lu = p_lu.data

        data2 = np.ma.zeros((data.shape[0], 4, data.shape[2], data.shape[3]))

        for t in range(data.shape[0]):
            for x in range(data.shape[2]):
                for y in range(data.shape[3]):
                    data2[t, 0, x, y] = data[t, 0, x, y]
                    data2[t, 1, x, y] = 0
                    data2[t, 2, x, y] = data[t, 1, x, y]
                    data2[t, 3, x, y] = data[t, 6, x, y] + \
                        data[t, 7, x, y] + data[t, 8, x, y]
        data2[data2 >= 1e+16] = 1e+20

        new_name = 'reduce_lu({}{})'.format(p_data.name, p_lu.name)
        return PhysArray(data2, name=new_name, dimensions=[p_data.dimensions[0], p_lu.dimensions[0], p_data.dimensions[2], p_data.dimensions[3]], units=p_data.units)


#=========================================================================
# soilpoolsFunction
#=========================================================================
class get_soilpoolsFunction(Function):
    key = 'get_soilpools'

    def __init__(self, p_data1, p_data2, p_data3, p_soilpool):
        super(get_soilpoolsFunction, self).__init__(
            p_data1, p_data2, p_data3, p_soilpool)

    def __getitem__(self, index):
        p_data1 = self.arguments[0][index]
        p_data2 = self.arguments[1][index]
        p_data3 = self.arguments[2][index]
        p_soilpool = self.arguments[3][index]

        data1 = p_data1.data
        data2 = p_data2.data
        data3 = p_data3.data
        soilpool = p_soilpool.data

        data = np.ma.zeros((data1.shape[0], 3, data1.shape[1], data1.shape[2]))

        data[:, 0, :, :] = data1
        data[:, 1, :, :] = data2
        data[:, 2, :, :] = data3

        data[data >= 1e+16] = 1e+20
        data = np.ma.masked_values(data, 1e+20)

        new_name = 'soilpools({}{}{}{})'.format(
            p_data1.name, p_data2.name, p_data3.name, p_soilpool.name)
        return PhysArray(data, name=new_name, dimensions=[p_data1.dimensions[0], p_soilpool.dimensions[0], p_data1.dimensions[1], p_data1.dimensions[2]], units=p_data1.units)


#=========================================================================
# nonwoodyvegFunction
#=========================================================================
class get_nonwoodyvegFunction(Function):
    key = 'get_nonwoodyveg'

    def __init__(self, p_pct_nat_pft, p_pct_crop, p_landfrac, p_landUse):
        super(get_nonwoodyvegFunction, self).__init__(
            p_pct_nat_pft, p_pct_crop, p_landfrac,p_landUse)

    def __getitem__(self, index):
        p_pct_nat_pft = self.arguments[0][index]
        p_pct_crop = self.arguments[1][index]
        p_landfrac = self.arguments[2][index]
        p_landUse = self.arguments[3][index]

        pct_nat_pft = p_pct_nat_pft.data
        pct_crop = p_pct_crop.data
        landfrac = p_landfrac.data
        landUse = p_landUse.data

        data = np.ma.zeros((p_pct_nat_pft.shape[0], 4, p_pct_nat_pft.shape[2], p_pct_nat_pft.shape[3]))
        if index is None:
            return data

        data[:, 0, :, :] = pct_nat_pft[:,12,:,:]+pct_nat_pft[:,13,:,:]+pct_nat_pft[:,14,:,:]
        for t in range(p_pct_nat_pft.shape[0]):
            for i in range(p_pct_nat_pft.shape[2]):
                for j in range(p_pct_nat_pft.shape[3]):
                    if landfrac[i,j] <= 1.0:
                        data[t, 1, i, j] = 0.0
                        if pct_crop[t,1,i,j] > 0.0: 
                            data[t, 2, i, j] = 100.0
                        else:
                            data[t, 2, i, j] = 0.0
                        data[t, 3, i, j] = 0.0
                    else:
                        data[t, 1, i, j] = 1e+20
                        data[t, 2, i, j] = 1e+20
                        data[t, 3, i, j] = 1e+20

        data[data >= 1e+16] = 1e+20
        data = np.ma.masked_values(data, 1e+20)

        new_name = 'get_nonwoodyveg({})'.format(
            p_pct_nat_pft.name)
        return PhysArray(data, name=new_name, dimensions=[p_pct_nat_pft.dimensions[0], p_landUse.dimensions[0], p_pct_nat_pft.dimensions[1], p_pct_nat_pft.dimensions[2]], units=p_pct_nat_pft.units)


#=========================================================================
# expand_latlonFunction
#=========================================================================
class expand_latlonFunction(Function):
    key = 'expand_latlon'

    def __init__(self, p_data1, p_lat, p_lon):
        super(expand_latlonFunction, self).__init__(p_data1, p_lat, p_lon)

    def __getitem__(self, index):
        p_data1 = self.arguments[0][index]
        p_lat = self.arguments[1][index]
        p_lon = self.arguments[2][index]

        data1 = p_data1.data
        lat = p_lat.data
        lon = p_lon.data

        data = np.ma.zeros((data1.shape[0], lat.shape[0], lon.shape[0]))

        for x in range(lat.shape[0]):
            for y in range(lon.shape[0]):
                data[:, x, y] = data1

        data[data >= 1e+16] = 1e+20
        data = np.ma.masked_values(data, 1e+20)

        new_name = 'expand_latlon({}{}{})'.format(
            p_data1.name, p_lat.name, p_lon.name)
        return PhysArray(data, name=new_name, dimensions=[p_data1.dimensions[0], p_lat.dimensions[0], p_lon.dimensions[0]], units=p_data1.units)


#=========================================================================
# ocean_basinFunction
#=========================================================================
class ocean_basinFunction(Function):
    key = 'ocean_basin'

    def __init__(self, p_data1, p_comp, p_basin):
        super(ocean_basinFunction, self).__init__(p_data1, p_comp, p_basin)

    def __getitem__(self, index):
        p_data1 = self.arguments[0][index]
        p_comp = self.arguments[1]
        p_basin = self.arguments[2][index]

        data1 = p_data1.data
        comp = int(p_comp)
        basin = p_basin.data

        data = np.ma.zeros(
            (data1.shape[0], data1.shape[4], data1.shape[3], basin.shape[0]))

        for t in range(data1.shape[0]):
            for x in range(data1.shape[4]):
                for y in range(data1.shape[3]):
                    data[t, x, y, 0] = data1[t, 1, comp, y, x]
                    data[t, x, y, 1] = data1[t, 0, comp, y, x] - \
                        data1[t, 1, comp, y, x]
                    data[t, x, y, 2] = data1[t, 0, comp, y, x]

        data[data >= 1e+16] = 1e+20
        data = np.ma.masked_values(data, 1e+20)

        new_name = 'ocean_basin({}{})'.format(p_data1.name, p_basin.name)
        return PhysArray(data, name=new_name, dimensions=[p_data1.dimensions[0], p_data1.dimensions[4], p_data1.dimensions[3], p_basin.dimensions[0]], units=p_data1.units)
