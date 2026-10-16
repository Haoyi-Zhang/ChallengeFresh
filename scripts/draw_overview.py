"""Vector drawing primitives; copied into each independent project generator."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch

plt.rcParams.update({'font.family':'STIXGeneral', 'mathtext.fontset':'stix',
                     'font.size':9, 'pdf.fonttype':42, 'ps.fonttype':42,
                     'text.usetex':False, 'axes.unicode_minus':False})
CM = 1 / 2.54

class Drawing:
    def __init__(self, bounds):
        x0,y0,x1,y1 = bounds
        self.fig = plt.figure(figsize=((x1-x0)*CM,(y1-y0)*CM))
        self.ax = self.fig.add_axes([0,0,1,1], xlim=(x0,x1), ylim=(y0,y1))
        self.ax.set_aspect('equal'); self.ax.axis('off')
        self.nodes = {}
        self.labels = []

    def text(self,x,y,label,size=9,ha='center',va='center'):
        artist=self.ax.text(x,y,label,fontsize=size,ha=ha,va=va,
                            linespacing=1.15,clip_on=False,zorder=4)
        self.labels.append([artist,None])
        return artist

    def box(self,name,x,y,w,h,label,dashed=False,shape='rect',size=9):
        style = {'edgecolor':'black','facecolor':'white','linewidth':.55,
                 'linestyle':(0,(4,3)) if dashed else 'solid', 'zorder':2}
        if shape == 'diamond':
            obj = Polygon([(x-w/2,y),(x,y+h/2),(x+w/2,y),(x,y-h/2)],**style)
        elif shape == 'circle': obj = Circle((x,y),w/2,**style)
        else: obj = Rectangle((x-w/2,y-h/2),w,h,**style)
        self.ax.add_patch(obj); self.text(x,y,label,size)
        self.labels[-1][1]=(x-w/2,y-h/2,x+w/2,y+h/2)
        self.nodes[name] = (x,y,w,h,shape)

    def point(self,name,side):
        x,y,w,h,_ = self.nodes[name]
        return {'n':(x,y+h/2),'s':(x,y-h/2),'e':(x+w/2,y),
                'w':(x-w/2,y),'nw':(x-w/2,y+h/2),
                'ne':(x+w/2,y+h/2),'c':(x,y)}[side]

    def line(self,points,dashed=False):
        xs,ys=zip(*points)
        self.ax.plot(xs,ys,color='black',linewidth=.55,
                     linestyle=(0,(4,3)) if dashed else 'solid',zorder=1)

    def arrow(self,p,q,dashed=False,via=()):
        points=[p,*via,q]
        if via:self.line(points[:-1],dashed)
        self.ax.add_patch(FancyArrowPatch(points[-2],points[-1],
                         arrowstyle='-|>',mutation_scale=7.5,linewidth=.55,
                         color='black',shrinkA=0,shrinkB=0,
                         linestyle=(0,(4,3)) if dashed else 'solid',zorder=1))

    def edge(self,a,b,sa='s',sb='n',**kwargs):
        self.arrow(self.point(a,sa),self.point(b,sb),**kwargs)

    def frame(self,x,y,w,h):
        self.ax.add_patch(Rectangle((x,y),w,h,fill=False,edgecolor='black',
                                   linewidth=.55,linestyle=(0,(4,3)),zorder=0))

    def save(self,out,name):
        # Fixed physical canvas: do not enlarge or rasterize the scientific figure.
        self.fig.canvas.draw()
        renderer=self.fig.canvas.get_renderer()
        x0,x1=self.ax.get_xlim();y0,y1=self.ax.get_ylim()
        for artist,node in self.labels:
            b=artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            if b.x0<x0-.02 or b.x1>x1+.02 or b.y0<y0-.02 or b.y1>y1+.02:
                raise ValueError(name+': clipped label '+repr(artist.get_text()))
            if node and (b.x0<node[0]-.02 or b.x1>node[2]+.02 or b.y0<node[1]-.02 or b.y1>node[3]+.02):
                raise ValueError(name+': label exceeds node '+repr(artist.get_text()))
        self.fig.savefig(out/(name+'.pdf'),format='pdf',
                         metadata={'Creator':'Python Matplotlib','Producer':None,
                                   'CreationDate':None,'ModDate':None})
        plt.close(self.fig)

def draw_all(out):
    out.mkdir(parents=True,exist_ok=True)
    d=Drawing((-2.35,-5.12,12.75,1.05))
    d.box('decl',0,0,4.4,1.7,'Declared source\n'+r'$\widetilde H_\infty(X\mid Z)\geq k$'+'\nmaps, kernels, radii, retries')
    d.box('fiber',5.2,0,4.4,1.7,'Observation/epoch entrance\n'+r'$+$ proof shadow $S$'+'\nuniform affine fibers under $U$')
    d.box('rank',10.4,0,4.4,1.7,'Residual rank\n'+r'$r=\mathrm{rank}(S;A)-\mathrm{rank}(S)$'+'\nworst-code $M(r,t,q)$')
    d.box('noise',5.2,-2.2,4.4,1.7,'Independent-BSC observation\ncoherent signal and\naffine-coset average')
    d.box('seq',10.4,-2.2,4.4,1.7,'Conditional epoch survival\nfinite product /\nadmission filter')
    d.box('transfer',10.4,-4.2,4.4,1.5,'One terminal transfer\n'+r'$\min\{1,2^{d-k}B+\epsilon\}$')
    d.edge('decl','fiber','e','w')
    d.edge('fiber','rank','e','w')
    d.edge('rank','seq')
    d.edge('fiber','noise')
    d.edge('noise','seq','e','w')
    d.edge('seq','transfer')
    d.save(out,'overview')

def main():
    import tempfile
    ap=argparse.ArgumentParser(description='Direct Python vector diagram of the affine-channel certificate transformations.')
    ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'figures')
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);draw_all(out)
            if not (args.output/'overview.pdf').is_file() or (out/'overview.pdf').read_bytes()!=(args.output/'overview.pdf').read_bytes():
                raise SystemExit('Missing/stale overview vector diagram')
        print('Overview vector diagram reproduces byte-for-byte.')
    else:draw_all(args.output)
if __name__=='__main__':main()
