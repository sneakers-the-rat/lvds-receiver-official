import numpy as np
from scipy.special import erfc, erfcinv
c=299792458; q=1.602176634e-19; kB=1.380649e-23; T=290
en=4.8e-9; inn=1.3e-15; GBP=1.6e9; Cin=2.3e-12
A0=3162.0; fa=GBP/A0
freq=np.linspace(0,3e9,30001); df=freq[1]-freq[0]
s=1j*2*np.pi*freq
A=A0/(1+s/(2*np.pi*fa))
for Rf,Cf in [(3300,0.45e-12),(3300,0.372e-12),(2200,None),(10000,None)]:
    if Cf is None:
        Cf=np.sqrt(Cin/(2*np.pi*GBP*Rf))/0.707
    Zf=Rf/(1+s*Rf*Cf)
    Zt=-Zf/((1+1/A)+s*Cin*Zf/A)
    # noise gain transfer for en: derive Hen = A*(1+sCinZf)/(1+sCinZf+A)
    Hen=A*(1+s*Cin*Zf)/(1+s*Cin*Zf+A)
    Izt=np.trapezoid(np.abs(Zt)**2,freq)
    Ihen=np.trapezoid(np.abs(Hen)**2,freq)
    Zt0=np.abs(Zt[10])
    Beff=Izt/Zt0**2
    sig_en=en*np.sqrt(Ihen)
    sig_j=np.sqrt(4*kB*T/Rf*Izt)
    sig_in=inn*np.sqrt(Izt)
    sig_tia=np.sqrt(sig_en**2+sig_j**2+sig_in**2)
    mag=np.abs(Zt); target=mag[10]/np.sqrt(2)
    idx=np.where((freq>1e6)&(mag<target))[0][0]
    f3=freq[idx]
    print(f"Rf={Rf} Cf={Cf*1e12:.3f}pF Zt0={Zt0:.0f} f3={f3/1e6:.1f}MHz Beff={Beff/1e6:.1f}MHz sig_en={sig_en*1e3:.3f}mV sigJ={sig_j*1e3:.3f}mV sigTIA={sig_tia*1e3:.3f}mV peakNG={np.max(np.abs(Hen)):.2f} tr={0.35/f3*1e9:.2f}ns")
    # Q at -34dBm 740
    R0=0.50; Pavg=10**(-34/10)*1e-3; er=10
    P1=2*Pavg*er/(er+1); P0=P1/er
    I1p=R0*P1; I0p=R0*P0; Id_out=0.1e-9
    for M in [10,20,35,50,70,100,150,200]:
        F=0.02*M+(2-1/M)*(1-0.02)
        Idp=Id_out/M
        def sig(Ip):
            shot=np.sqrt(2*q*(Ip+Idp)*M**2*F*Beff)*Zt0
            return np.sqrt(sig_tia**2+shot**2)
        s1,s0=sig(I1p),sig(I0p)
        Qv=(I1p-I0p)*M*Zt0/(s1+s0)
        ber=0.5*erfc(Qv/np.sqrt(2))
        print(f"  M={M} F={F:.2f} s1={s1*1e3:.2f} s0={s0*1e3:.2f} mV Q={Qv:.2f} BER={ber:.2e}")

print("\n--- sensitivity scan (Rf=3.3k Cf=0.45) ---")
# recompute for that config quickly by re-running functions inline: use last? redo
Rf,Cf=3300,0.45e-12
Zf=Rf/(1+s*Rf*Cf)
Zt=-Zf/((1+1/A)+s*Cin*Zf/A)
Hen=A*(1+s*Cin*Zf)/(1+s*Cin*Zf+A)
Izt=np.trapz(np.abs(Zt)**2,freq); Ihen=np.trapz(np.abs(Hen)**2,freq)
Zt0=np.abs(Zt[10]); Beff=Izt/Zt0**2
sig_tia=np.sqrt((en*np.sqrt(Ihen))**2+4*kB*T/Rf*Izt+(inn*np.sqrt(Izt))**2)
print("sig_tia mV",sig_tia*1e3,"Beff MHz",Beff/1e6)
from scipy.optimize import brentq
def Qof(Pavg,R0,M):
    er=10; P1=2*Pavg*er/(er+1); P0=P1/er; I1p=R0*P1; I0p=R0*P0; Idp=0.1e-9/M
    F=0.02*M+(2-1/M)*0.98
    def sg(Ip): return np.sqrt(sig_tia**2+2*q*(Ip+Idp)*M**2*F*Beff*Zt0**2)
    return (I1p-I0p)*M*Zt0/(sg(I1p)+sg(I0p))
for R0,lab in [(0.50,'740'),(0.37,'630')]:
    Ms=np.arange(5,201,1)
    for Qt in [np.sqrt(2)*erfcinv(2*1e-6), np.sqrt(2)*erfcinv(2*1e-9)]:
        best=None
        for M in Ms:
            try:
                f=lambda lp: Qof(10**(lp/10)*1e-3,R0,M)-Qt
                root=brentq(f,-70,-20)
            except Exception as e:
                root=np.nan
            if best is None or root<best[1]: best=(M,root)
        print(lab,"Qtarget",Qt,"best M,sens dBm",best)
        # Q at -34 for best M
        print("  Q@-34 bestM",Qof(10**(-3.4)*1e-3,R0,best[0]))
    # sensitivity per specific M
    for M in [20,50,70,100]:
        Qt=np.sqrt(2)*erfcinv(2*1e-6)
        root=brentq(lambda lp: Qof(10**(lp/10)*1e-3,R0,M)-Qt,-70,-20)
        print(f"  {lab} M={M} sens1e-6={root:.2f} dBm")
