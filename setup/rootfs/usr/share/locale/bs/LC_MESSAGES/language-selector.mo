��    ;      �  O   �        -   	  )   7     a     h  �   w  v   �  8   t  K   �  N   �     H     Z     o  =   �  +   �  /   �  	        )     /  D   7  k   |  (   �  �  	     �
     �
  	   �
        �        �     �     �     �  !        7     ?     P     i     �  }   �  0     �  P  0   �  D     �   `  �   �  �  n  N  h  �   �  X   �     �     �            E   *  '   p     �  @   �  /   �       �  #  P     D   b     �     �  �   �  �   G  F   �  R     Q   k     �     �     �  G     /   K  3   {     �     �     �  <   �  s     6   w  �  �     e     �     �     �  �   �     �     �     �     �  "   �     �     �  #      %   5      [   w   u   @   �   z  .!  /   �"  <   �"  a   #  z   x#    �#  L  &  �   N'  f   5(     �(     �(  
   �(     �(  F   �(  .   ,)     [)  :   b)  *   �)     �)           *                  2   .         !   +           7   &                1       -       '   ,          )       ;   5      6       $          	                         0                           8               9      3       
   4      (   %          /         #   :         "    %(INSTALL)d to install %(INSTALL)d to install %(REMOVE)d to remove %(REMOVE)d to remove %s, %s <b>Example</b> <big><b>Checking available language support</b></big>

The availability of translations or writing aids can differ between languages. <small><b>Drag languages to arrange them in order of preference.</b>
Changes take effect next time you log in.</small> <small>Changes take effect next time you log in.</small> <small>Use the same format choice for startup and the login screen.</small> <small>Use the same language choices for startup and the login screen.</small> Apply System-Wide Chinese (simplified) Chinese (traditional) Configure multiple and native language support on your system Could not install the full language support Could not install the selected language support Currency: Date: Details Display numbers, dates and currency amounts in the usual format for: Failed to apply the '%s' format
choice. The examples may show up if you
close and re-open Language Support. Failed to authorize to install packages. If you need to type in languages, which require more complex input methods than just a simple key to letter mapping, you may want to enable this function.
For example, you will need this function for typing Chinese, Japanese, Korean or Vietnamese.
The recommended value for Ubuntu is "IBus".
If you want to use alternative input method systems, install the corresponding packages first and then choose the desired system here. Incomplete Language Support Install / Remove Languages... Installed Installed Languages It is impossible to install or remove any software. Please use the package manager "Synaptic" or run "sudo apt-get install -f" in a terminal to fix this issue at first. Keyboard input method system: Language Language Support Language for menus and windows: No language information available Number: Regional Formats Session Restart Required Set system default language Software database is broken Some translations or writing aids available for your chosen languages are not installed yet. Do you want to install them now? System policy prevented setting default language The language support files for your selected language seem to be incomplete. You can install the missing components by clicking on "Run this action now" and follow the instructions. An active internet connection is required. If you would like to do this at a later time, please use Language Support instead (click the icon at the very right of the top bar and select "System Settings... -> Language Support"). The language support is not installed completely The new language settings will take effect once you have logged out. The system does not have information about the available languages yet. Do you want to perform a network update to get them now?  This is perhaps a bug of this application. Please file a bug report at https://bugs.launchpad.net/ubuntu/+source/language-selector/+filebug This setting only affects the language your desktop and applications are displayed in. It does not set the system environment, like currency or date format settings. For that, use the settings in the Regional Formats tab.
The order of the values displayed here decides which translations to use for your desktop. If translations for the first language are not available, the next one in this list will be tried. The last entry of this list is always "English".
Every entry below "English" will be ignored. This will set the system environment like shown below and will also affect the preferred paper format and other region specific settings.
If you want to display the desktop in a different language than this, please select it in the "Language" tab.
Hence you should set this to a sensible value for the region in which you are located. Usually this is related to an error in your software archive or software manager. Check your preferences in Software Sources (click the icon at the very right of the top bar and select "System Settings... -> Software Sources"). When a language is installed, individual users can choose it in their Language settings. _Install _Remind Me Later _Update alternative datadir check for the given package(s) only -- separate packagenames by comma don't verify installed language support none output all available language support packages for all languages show installed packages as well as missing ones target language code Project-Id-Version: language-selector
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2016-09-01 11:27+0000
Last-Translator: Kenan Dervišević <kenan@dkenan.com>
Language-Team: Bosnian <bs@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=3; plural=n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2;
X-Launchpad-Export-Date: 2018-04-14 13:43+0000
X-Generator: Launchpad (build 18610)
Language: bs
 %(INSTALL)d za instalaciju %(INSTALL)d za instalaciju %(INSTALL)d za instalaciju %(REMOVE)d za brisanje %(REMOVE)d za brisanje %(REMOVE)d za brisanje %s, %s <b>Primjer</b> <big><b>Provjera raspoložive jezičke podrške</b></big>

Raspoloživost prijevoda i alatki za pisanje se razlikuje od jezika do jezika. <small><b>Prevuci jezike za njihovo sortiranje po redoslijedu preferencije.</b>
Promjene će imati efekta pri sljedećoj prijavi.</small> <small>Promjene stupaju na snagu kod iduće prijave na sistem.</small> <small>Koristi isti izbor formata za pokretanje i za ekran prijavljivanja.</small> <small>Koristi isti izbor jezika za pokretanje i za ekran prijavljivanja.</small> Primijeni na sistem Kineski (pojednostavljen) Kineski (tradicionalni) Podesite višejezičnu i podršku za vlastitog jezika na vašem sistemu Nije moguće instalirati punu jezičku podršku Nije moguće instalirati podršku za odabrani jezik Valuta: Datum: Detalji Prikaži brojeve, datume i valutu u uobičajenom formatu za: Neuspjela primjena izbora '%s' formata
Primjeri se mogu pokazati ako zatvorite
i ponovo otvorite jezičku podršku. Nisam uspio da dam ovlašćenje za instalaciju paketa. Ako je potrebno pisati u jezicima, koji zahtijevaju složenije metode unosa nego samo jednostavno mapiranje tastera u slovo, vi možete omogućiti ovu funkciju.
Na primjer, trebat ćete ovu funkciju za tipkanje na kineski, japanski, korejski ili vijetnamski.
Preporučena vrijednost za Ubuntu je "IBUS".
Ako želite koristiti alternativne sisteme za metodu unosa, instalirati odgovarajuće pakete, a zatim odaberite željeni sistem ovdje. Nekompletna jezička podrška Instaliraj / odstrani jezike... Instalirano Instalirani jezici Nemoguće je instalirati ili ukloniti bilo koji program. Molim da najprije iskoristite "Synaptic" upravnika paketima ili izvršite "sudo apt-get install -f" u terminalu kako biste otklonili problem. Način unosa s tastature: Jezik Jezička podrška Jezik za menije i prozore Nema dostupne informacije o jeziku Broj: Regionalni formati Neophodno ponovno pokretanje sesije Postavi podrazumijevani jezik sistema Baza paketa je neispravna Dio prevoda ili pomoći pri pisanju dostupnih za Vaš jezik još nije instaliran. Da li želite da ih sada instalirate? Pravila sistema spriječila postavljanje podrazumijevanog jezika Jezička podrška za vaš jezik izgleda nekompletna. Možete instalirati nedostajuć komponente ako kliknete na "Izvrši ovui akciju sada " i pratite instrukcije. Potrebne je aktivna internet konekcija. Ako želite da to uradite kasnije, koristit opciju Jezička podrška  (kliknite ikonu na desnoj strani trake na vrhu i odaberite "Sistemske postavke ... -> Jezička podrška") Jezička podrška nije instalirana u potpunosti Nove jezičke postavke će stupiti na snagu kad se odjavite. Sistem nema informacija o raspoloživim jezicima. Želite li mrežno ažuriranje da ih dobijete?  Ovo je vjerovatno greška u programu. Prijavite je na https://bugs.launchpad.net/ubuntu/+source/language-selector/+filebug Ovo podešavanje utiče samo na jezik vašeg desktopa i aplikacije koje su prikazane u njemo To ne podešava sistemsko okruženje, kao što su valuta ili format datuma. Zbog toga, koristite podešavanja u kartici Regionalni Formati.
Redosled vrijednosti prikazanih ovdje odlučuje koje prijevode da koristite za vaše radno okruženje. Ako prijevodi za prvi jezik nisu na raspolaganju, sljedeći na ovoj listi će biti isprobani. Posljednji unos ove liste je uvijek "engleski".
Svaki unos ispod "engleski" će biti ignorisan. Ovo će podesiti okruženje sistema kao što je prikazano ispod i takođe će uticati na željeni format papira i ostale postavke specifičnu oblast.
Ako želite da prikažete desktop u drugom jeziku od ovog, molimo Vas izaberite je u "Jezik" kartici.
Dakle trebalo bi da podesite na razumnu vrijednost za region u kome se nalazite. Obično ovo predstavlja grešku u vašoj softverskoj arhivi ili menadžeru softvera. Provjerite postavke u izvorima softvera (kliknite ikonu na desnoj strani trake na vrhu i odaberite "Sistemske postavke ... -> Softverski izvori") Nakon što je jezik instaliran, individualni korisnici ga mogu odabrati u svojim jezičkim postavkama. _Instaliraj _Podsjeti me kasnije _Ažuriraj alternativni imenik podataka provjera samo za naveden(e) paket(e) -- odvojite nazive paketa zarezom nemoj provjeriti instaliranu jezičku podršku ništa ispisuje sve dostupne pakete podrške jezika za sve jezike prikaži instalirane i nedostajuće pakete oznaka odredišnog jezika 