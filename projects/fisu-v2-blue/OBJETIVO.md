# fisu-v2-blue — el dólar blue reemplaza al ORO, y todo pop-up con su imagen (E14b B14 + B9)

Pedido del dueño (2026-10-14), spec `Docs/PLAN-v2-E14b-correcciones.md` del juego, secciones B9 y B14 y
decisiones D8/D9:

- **B14:** no puede quedar rastro de que el dólar blue se llamó ORO. Toda imagen que muestre la moneda premium
  como oro (lingotes, monedas de oro como premium) se reemplaza por una en estética `ui_dolar_blue`: billetes
  azules/turquesa, fajos con faja de papel, el signo $ grande, sin próceres ni texto.
- **B9 / D9:** todo pop-up lleva una imagen principal, grande, vistosa y centrada.
- **D8:** se integran directo, sin pasar por la aprobación del dueño; si alguna no le gusta, la cambia después.

Motor: Gemini, modelo **Flash** (elegirlo a mano en el selector del Chrome aislado antes de correr).
Estilo: el de los premios aprobados de `fisu-v2-premios` (contorno negro grueso, colores planos, fondo blanco).
Referencias (una por prompt): `references/ui_dolar_blue.png` (la moneda premium, para todo lo que es blue),
`references/rw_mystery_all.png` (la pila de premios, para las imágenes de los packs) y `references/style/icon.png`
(el estilo base). `references/cow-evolution-popup.webp` es la referencia de composición del pop-up (no se adjunta).
Salida `game-asset` en 384/512/768 (las de pop-up se muestran grandes). Destino: `FisuEvolution/Tools/asset-pipeline/dropbox/`.

## Lista

| # | clave | destino en el juego | por qué |
|---|---|---|---|
| 01 | `ui_blue_pack_small` | Tienda, estante de blue: pack chico (`…iap.oro_small`) | `StoreView` dibuja los 3 packs con `OroIcon` → `ui_oro`, el lingote de oro |
| 02 | `ui_blue_pack_medium` | Tienda: pack mediano (`…iap.oro_medium`) | ídem; además los 3 packs se distinguen por tamaño |
| 03 | `ui_blue_pack_large` | Tienda: pack grande (`…iap.oro_large`) | ídem |
| 04 | `rw_pack_mudanza` | Pop-up Moving Day Pack (`OfferSheet`, oferta `mudanza`) | B9.4: imagen de lo que trae (blue, producción, 3 paquetes de la Aduana); hoy sin imagen |
| 05 | `rw_pack_bienvenida` | Pop-up oferta Bienvenida (`OfferSheet`) | mismo pop-up que la Mudanza, sin imagen (blue, producción, cofre de skins) |
| 06 | `rw_pack_renacer` | Pop-up oferta Renacer (`OfferSheet`) | ídem (blue, producción, ingresos ×3) |
| 07 | `rw_reencarnar` | Pop-up Reencarnar (`PrestigeView`) | sin imagen principal; paga en blue |
| 08 | `rw_mattress_hero` | Pop-up del Colchón (`MattressPopupView`), arriba | B9.3: «arriba, una imagen del colchón»; `pickup_mattress` es un sprite de tablero de 384 px |
| 09 | `ui_notif_campana` | `NotificationPermissionCard` | hoy un SF Symbol (regla del dueño: cero SF Symbols) |
| 10 | `ui_save_rescate` | `SaveRecoveryView` | sin imagen |
| 11 | `ui_reset_demolicion` | `ResetGameFlowView` | sin imagen |

## Lo que NO se genera (decidido con evidencia, 2026-10-14)

- **`ui_oro` (lingote):** ya existe `ui_dolar_blue`. Es código: `OroIcon` (GameArt.swift) tiene que usar
  `ui_dolar_blue` (Tienda de blue, botón y pop-up de Reencarnar, Stats) y el asset `ui_oro` se borra.
- **`wheel_seg_jackpot` (lingote sobre monedas):** está en `assets_manifest.json` pero ningún `.swift` lo usa.
  Se borra del atlas y del manifest.
- **`icon_ui_oro_*.mov` (10 íconos animados de la Tienda de blue):** se miraron los cuadros: no muestran oro
  (mano robot, caja, calendario, sillas, ruleta, bolsa de monedas…). Sólo el nombre: renombrar en código y en
  `loops_manifest.json`.
- **Monedas doradas (`ui_coin`, `ui_coin_plus`, `rw_coins`, `rw_income_mult`, `ui_up_income`, `ui_up_offline`,
  `ui_shop_*`, las de `rw_mystery_all`, `ui_offer_renacer`, `cine_reencarnacion`):** son la moneda COMÚN del juego
  (la del HUD, «29,3K»), no la premium. No se tocan.
- **`ui_up_golden`** (mejora «Toque de suerte», `luckyTouch`): moneda común con estrella; «golden» es la mecánica
  del toque dorado, no la moneda. Si el texto dice «oro», se cambia el texto.
- **`ui_trophy_gold`:** nivel de trofeo de logros, no moneda.
- **Skins `*__oro` de los atlas:** la rareza, no la moneda (B14 la decide en textos; los nombres de archivo los
  renombra el código si hace falta, sin regenerar).
- **«Todos los premios juntos»:** ya existe `rw_mystery_all` (tesoros con el mate, aprobado). Es código: ponerla
  grande arriba de «What you can get» (Ruleta) y «What could be inside» (Colchón).
- **Ruleta cortada:** el arte está entero (`wheel_frame`, `wheel_icon`, `obj_ruleta_espera/premio.mov` muestran la
  ruleta completa); el corte es de layout (`WheelView`: `.frame(WheelStage.size)` + `.clipped()`). Es código.
- **Eventos, Regalos, Diario, Offline, Skin, Especial, Caja, Cofre, Carrera, Ficha de personaje, Ascensor:** ya
  tienen imagen (`ui_event_*`, `RewardIllustration`, `pickup_package`, `ui_chest_closed`, retratos). El de eventos
  hoy usa la ilustración del premio: puede pasar a `ui_event_*`, que existen.
- **Corte de anuncio (`RewardedInterstitialIntroView`):** usa un SF Symbol del premio; es código pasar a
  `RewardIllustration`, que ya existe para todos los premios.
