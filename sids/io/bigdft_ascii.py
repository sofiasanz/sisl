"""
Sile object for reading/writing ascii files from BigDFT
"""

from __future__ import division, print_function

# Import sile objects
from sids.io.sile import *

# Import the geometry object
from sids import Geometry, Atom, SuperCell
from sids import Bohr

import numpy as np

__all__ = ['BigDFTASCIISile']


class BigDFTASCIISile(Sile):
    """ ASCII file object for BigDFT """
    # These are the comments

    def _setup(self):
        """ Initialize for `BigDFTASCIISile` """
        self._comment = ['#','!']


    def read_geom(self):
        """ Reads a supercell from the Sile """
        if not hasattr(self,'fh'):
            # The file-handle has not been opened
            with self:
                return self.read_geom()

        # 1st line is arbitrary
        self.readline(True)
        # Read dxx, dyx, dyy
        dxx, dyx, dyy = map(float,self.readline().split()[:3])
        # Read dzx, dzy, dzz
        dzx, dzy, dzz = map(float,self.readline().split()[:3])

        # options for the ASCII format
        is_frac = False
        is_angdeg = False
        is_bohr = False

        xyz = []
        spec = []

        # Now we need to read through and find keywords
        try:
            while True:
                
                # Read line also with comment
                l = self.readline(True)

                # Empty line, means EOF
                if l == '': break
                # too short, continue
                if len(l) < 1: continue

                # Check for keyword
                if l[1:].startswith('keyword:'):
                    if 'reduced' in l:
                        is_frac = True
                    if 'angdeg' in l:
                        is_angdeg = True
                    if 'bohr' in l or 'atomic' in l:
                        is_bohr = True
                    continue

                elif l[0] in self._comment:
                    
                    # this is a comment, cycle
                    continue
                
                # Read atomic coordinates
                ls = l.split()

                # The first three are the coordinates
                xyz.append(map(float,ls[:3]))
                # The 4th is the specie, [5th is tag]
                s = ls[3]
                t = s
                if len(ls) > 4:
                    t = ls[4]
                spec.append(Atom(s,tag=t))
                
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
        except:
            pass

        if is_bohr:
            dxx /= Bohr
            dyx /= Bohr
            dyy /= Bohr
            if not is_angdeg:
                dzx /= Bohr
                dzy /= Bohr
                dzz /= Bohr

        # Create the supercell
        if is_angdeg:
            # The input is in skewed axis
            sc = SuperCell([dxx,dyx,dyy,dzx,dzy,dzz])
        else:
            sc = SuperCell([[dxx,0,0],[dyx,dyy,0],[dzx,dzy,dzz]])

        # Now create the geometry
        xyz = np.array(xyz,np.float64)

        if is_frac:
            # Transform from fractional to actual
            # coordinates
            xyz = np.dot(xyz,sc.cell.T)
            
        elif is_bohr:
            # Not when fractional coordinates are used
            # the supercell conversion takes care of
            # correct unit
            xyz /= Bohr

        return Geometry(xyz,atoms=spec,sc=sc)
        

    def write_geom(self,geom,fmt='.5f'):
        """ Writes the geometry to the contained file """
        # Check that we can write to the file
        sile_raise_write(self)

        if not hasattr(self,'fh'):
            # The file-handle has not been opened
            with self:
                return self.write_geom(geom,fmt)

        # Write out the cell
        self._write('# Created by sids\n')
        # We write the cell coordinates as the cell coordinates
        fmt_str = '{{:{0}}} '.format(fmt)*3 + '\n'
        self._write(fmt_str.format(geom.cell[0,0],geom.cell[1,0],geom.cell[1,1]))
        self._write(fmt_str.format(*geom.cell[2,:]))

        # This also denotes 
        self._write('#keyword: angstroem\n')

        self._write('# Geometry containing: '+str(len(geom))+' atoms\n')

        f1_str = '{{1:{0}}}  {{2:{0}}}  {{3:{0}}} {{0:2s}}\n'.format(fmt)
        f2_str = '{{2:{0}}}  {{3:{0}}}  {{4:{0}}} {{0:2s}} {{1:s}}\n'.format(fmt)

        for ia,a,isp in geom.iter_species():
            if a.symbol != a.tag:
                self._write(f2_str.format(a.symbol,a.tag,*geom.xyz[ia,:]))
            else:
                self._write(f1_str.format(a.symbol,*geom.xyz[ia,:]))
        # Add a single new line
        self._write('\n')


    
if __name__ == "__main__":
    # Create geometry
    alat = 3.57
    dist = alat * 3. **.5 / 4
    C = Atom(Z=6,R=dist * 1.01,orbs=2)
    sc = SuperCell(np.array([[0,1,1],
                             [1,0,1],
                             [1,1,0]],np.float64) * alat/2)
    geom = Geometry(np.array([[0,0,0],[1,1,1]],np.float64)*alat/4,
                    atoms = C, sc=sc)
    # Write stuff
    print(geom)
    geom.write(BigDFTASCIISile('diamond.ascii','w'))
    geomr = BigDFTASCIISile('diamond.ascii','r').read_geom()
    print(geomr)
    print(geomr.cell)
    print(geomr.xyz)
