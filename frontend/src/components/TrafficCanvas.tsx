import React, { useRef, useEffect } from 'react';
import { SimulationEngine } from '../simulation/SimulationEngine';
import type { Vehicle, LightState } from '../simulation/types';

interface TrafficCanvasProps {
  engine: SimulationEngine;
}

export const TrafficCanvas: React.FC<TrafficCanvasProps> = ({ engine }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const render = () => {
      // Dimensions
      const w = canvas.width;
      const h = canvas.height;

      // Color scheme according to night mode
      const isNight = engine.nightMode;
      const colors = isNight
        ? {
            grass: '#090d16', // deep space slate
            asphalt: '#1e293b', // slate asphalt
            lawn: '#0b0f19', // deep dark matte gray-teal
            bitumen: '#0b0f19', // sidewalks
            curb: '#1e293b', // curb
            marking: '#334155', // dim white markings
            yellow: '#ca8a04', // dark yellow markings
            housing: '#020617', // black housing
            redLight: '#ef4444',
            redLightDim: '#7f1d1d',
            orangeLight: '#f97316',
            orangeLightDim: '#7c2d12',
            greenLight: '#10b981',
            greenLightDim: '#064e3b',
          }
        : {
            grass: '#111827', // dark slate-gray background
            asphalt: '#1e293b', // slate-blue asphalt
            lawn: '#0f172a', // dark zinc background
            bitumen: '#090d16', // sidewalks
            curb: '#334155', // curb border
            marking: 'rgba(255, 255, 255, 0.65)', // subtle markings
            yellow: 'rgba(202, 138, 4, 0.7)', // subtle yellow center line
            housing: '#0d121f', // light box housing
            redLight: '#ef4444',
            redLightDim: '#7f1d1d',
            orangeLight: '#f97316',
            orangeLightDim: '#7c2d12',
            greenLight: '#10b981',
            greenLightDim: '#064e3b',
          };

      // 1. Clear background
      ctx.fillStyle = colors.grass;
      ctx.fillRect(0, 0, w, h);

      // Save context state, translate to center and scale to match Cartesian
      ctx.save();
      ctx.translate(w / 2, h / 2);
      ctx.scale(1, -1); // Y goes up

      // 2. Draw Asphalt Roads
      ctx.fillStyle = colors.asphalt;
      ctx.fillRect(-450, -70, 900, 140); // Horizontal Road
      ctx.fillRect(-70, -350, 140, 700); // Vertical Road
      ctx.fillRect(-130, -130, 260, 260); // Intersection center including rounded corners area

      // 3. Draw Sidewalks (Corners)
      const drawSidewalkCorner = (sx: number, sy: number) => {
        // Remplissage de la pelouse extérieure
        ctx.fillStyle = colors.lawn;
        ctx.fillRect(
          sx === -1 ? -450 : 130,
          sy === -1 ? -350 : 130,
          320,
          220
        );

        // Remplissage du trottoir (bitume)
        ctx.fillStyle = colors.bitumen;
        ctx.beginPath();
        ctx.moveTo(70 * sx, 350 * sy);
        ctx.lineTo(70 * sx, 130 * sy);
        // Courbe du trottoir intérieur
        ctx.arcTo(70 * sx, 70 * sy, 130 * sx, 70 * sy, 60);
        ctx.lineTo(450 * sx, 70 * sy);
        ctx.lineTo(450 * sx, 130 * sy);
        ctx.lineTo(130 * sx, 130 * sy);
        ctx.lineTo(130 * sx, 350 * sy);
        ctx.closePath();
        ctx.fill();

        // Dessin de la bordure (curb)
        ctx.strokeStyle = colors.curb;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(70 * sx, 350 * sy);
        ctx.lineTo(70 * sx, 130 * sy);
        ctx.arcTo(70 * sx, 70 * sy, 130 * sx, 70 * sy, 60);
        ctx.lineTo(450 * sx, 70 * sy);
        ctx.stroke();
      };

      // Top-Left, Top-Right, Bottom-Left, Bottom-Right
      drawSidewalkCorner(-1, 1);
      drawSidewalkCorner(1, 1);
      drawSidewalkCorner(-1, -1);
      drawSidewalkCorner(1, -1);

      // 4. Draw Center Double Yellow Lines
      ctx.strokeStyle = colors.yellow;
      ctx.lineWidth = 2;
      
      const drawCenterLine = (x1: number, y1: number, x2: number, y2: number, offset: number) => {
        ctx.beginPath();
        if (x1 === x2) {
          ctx.moveTo(x1 - offset, y1);
          ctx.lineTo(x2 - offset, y2);
          ctx.moveTo(x1 + offset, y1);
          ctx.lineTo(x2 + offset, y2);
        } else {
          ctx.moveTo(x1, y1 - offset);
          ctx.lineTo(x2, y2 - offset);
          ctx.moveTo(x1, y1 + offset);
          ctx.lineTo(x2, y2 + offset);
        }
        ctx.stroke();
      };

      drawCenterLine(-450, 0, -100, 0, 2); // Left West
      drawCenterLine(100, 0, 450, 0, 2);  // Right East
      drawCenterLine(0, -350, 0, -100, 2); // Bottom South
      drawCenterLine(0, 100, 0, 350, 2);   // Top North

      // 5. Draw Lane Dashed Markings
      ctx.strokeStyle = colors.marking;
      ctx.lineWidth = 1.5;
      ctx.setLineDash([15, 15]);

      // Horizontal dashed
      ctx.beginPath();
      ctx.moveTo(-450, -35); ctx.lineTo(-100, -35);
      ctx.moveTo(-450, 35); ctx.lineTo(-100, 35);
      ctx.moveTo(100, -35); ctx.lineTo(450, -35);
      ctx.moveTo(100, 35); ctx.lineTo(450, 35);
      // Vertical dashed
      ctx.moveTo(-35, -350); ctx.lineTo(-35, -100);
      ctx.moveTo(35, -350); ctx.lineTo(35, -100);
      ctx.moveTo(-35, 100); ctx.lineTo(-35, 350);
      ctx.moveTo(35, 100); ctx.lineTo(35, 350);
      ctx.stroke();
      ctx.setLineDash([]); // Reset dashed

      // 6. Draw Crosswalks (Zebras)
      ctx.fillStyle = colors.marking;
      const drawCrosswalk = (cx: number, cy: number, isVertical: boolean) => {
        const stripeWidth = 12;
        const stripeLength = 40;
        const stripeSpacing = 20;

        for (let i = 0; i < 7; i++) {
          const offset = -60 + i * stripeSpacing;
          if (isVertical) {
            ctx.fillRect(offset, cy - stripeLength / 2, stripeWidth, stripeLength);
          } else {
            ctx.fillRect(cx - stripeLength / 2, offset, stripeLength, stripeWidth);
          }
        }
      };

      drawCrosswalk(0, 105, true);   // North Crosswalk
      drawCrosswalk(0, -105, true);  // South Crosswalk
      drawCrosswalk(105, 0, false);  // East Crosswalk
      drawCrosswalk(-105, 0, false); // West Crosswalk

      // 7. Draw Stop Lines
      ctx.strokeStyle = colors.marking;
      ctx.lineWidth = 5;
      
      ctx.beginPath();
      ctx.moveTo(-135, -70); ctx.lineTo(-135, 0);   // East flow stop line (incoming from West)
      ctx.moveTo(135, 70); ctx.lineTo(135, 0);     // West flow stop line (incoming from East)
      ctx.moveTo(0, -135); ctx.lineTo(70, -135);   // North flow stop line (incoming from South)
      ctx.moveTo(0, 135); ctx.lineTo(-70, 135);    // South flow stop line (incoming from North)
      ctx.stroke();

      // 8. Draw Central Island (Rond-point)
      ctx.fillStyle = colors.curb;
      ctx.beginPath();
      ctx.arc(0, 0, 22, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = colors.grass;
      ctx.beginPath();
      ctx.arc(0, 0, 18, 0, Math.PI * 2);
      ctx.fill();

      // 9. Draw Lane Arrows
      ctx.fillStyle = colors.marking;
      const drawArrow = (x: number, y: number, angleDeg: number) => {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate((angleDeg * Math.PI) / 180);
        
        ctx.beginPath();
        ctx.moveTo(-15, -3);
        ctx.lineTo(5, -3);
        ctx.lineTo(5, -8);
        ctx.lineTo(15, 0);
        ctx.lineTo(5, 8);
        ctx.lineTo(5, 3);
        ctx.lineTo(-15, 3);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      };

      drawArrow(-250, -35, 0);   // Eastbound arrow
      drawArrow(250, 35, 180);   // Westbound arrow
      drawArrow(35, -250, 90);   // Northbound arrow
      drawArrow(-35, 250, 270);  // Southbound arrow

      // 10. Draw Vehicles
      engine.vehicles.forEach((v: Vehicle) => {
        ctx.save();
        ctx.translate(v.x, v.y);
        ctx.rotate((v.heading * Math.PI) / 180);

        // Vehicle Base Dimensions
        const vLength = v.length;
        const vWidth = v.width;

        // Draw Wheels
        ctx.fillStyle = '#1e293b';
        // Wheels Positions (rear/front left/right)
        const wheelW = 10;
        const wheelH = 4;
        ctx.fillRect(-vLength / 3 - wheelW / 2, -vWidth / 2 - 2, wheelW, wheelH);
        ctx.fillRect(vLength / 3 - wheelW / 2, -vWidth / 2 - 2, wheelW, wheelH);
        ctx.fillRect(-vLength / 3 - wheelW / 2, vWidth / 2 - 2, wheelW, wheelH);
        ctx.fillRect(vLength / 3 - wheelW / 2, vWidth / 2 - 2, wheelW, wheelH);

        // Draw Body
        ctx.fillStyle = v.color;
        // Rounded car body
        ctx.beginPath();
        ctx.roundRect(-vLength / 2, -vWidth / 2, vLength, vWidth, 5);
        ctx.fill();
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Roof / Windshield
        ctx.fillStyle = isNight ? '#1e293b' : '#94a3b8';
        ctx.beginPath();
        ctx.roundRect(-vLength / 5, -vWidth / 2 + 2, vLength * 0.5, vWidth - 4, 3);
        ctx.fill();

        // Headlights (glowing in night mode)
        if (isNight) {
          // Glow effect
          ctx.save();
          ctx.shadowColor = '#fef08a';
          ctx.shadowBlur = 15;
          ctx.fillStyle = '#fef08a';
          ctx.beginPath();
          ctx.arc(vLength / 2 - 2, -vWidth / 3, 3, 0, Math.PI * 2);
          ctx.arc(vLength / 2 - 2, vWidth / 3, 3, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();

          // Light beams (translucent yellow cones)
          ctx.fillStyle = 'rgba(254, 240, 138, 0.12)';
          ctx.beginPath();
          ctx.moveTo(vLength / 2, -vWidth / 3);
          ctx.lineTo(vLength / 2 + 120, -vWidth / 3 - 35);
          ctx.lineTo(vLength / 2 + 120, vWidth / 3 + 35);
          ctx.lineTo(vLength / 2, vWidth / 3);
          ctx.closePath();
          ctx.fill();
        } else {
          // Regular headlights
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(vLength / 2 - 3, -vWidth / 3 - 1, 3, 3);
          ctx.fillRect(vLength / 2 - 3, vWidth / 3 - 2, 3, 3);
        }

        // Brake Lights
        ctx.fillStyle = v.isBraking ? '#ef4444' : '#7f1d1d';
        if (v.isBraking) {
          ctx.save();
          ctx.shadowColor = '#ef4444';
          ctx.shadowBlur = 10;
          ctx.beginPath();
          ctx.arc(-vLength / 2 + 2, -vWidth / 3, 3, 0, Math.PI * 2);
          ctx.arc(-vLength / 2 + 2, vWidth / 3, 3, 0, Math.PI * 2);
          ctx.fill();
          ctx.restore();
        } else {
          ctx.fillRect(-vLength / 2, -vWidth / 3 - 1, 3, 2);
          ctx.fillRect(-vLength / 2, vWidth / 3 - 1, 3, 2);
        }

        // Blinkers (Orange blinking)
        if (v.blinkState) {
          ctx.fillStyle = '#f97316';
          ctx.save();
          ctx.shadowColor = '#f97316';
          ctx.shadowBlur = 8;
          
          if (v.turnIntention === 'LEFT') {
            // Blink left lights (top side in rotation coordinates)
            ctx.beginPath();
            ctx.arc(vLength / 2 - 3, vWidth / 2 - 2, 2.5, 0, Math.PI * 2);
            ctx.arc(-vLength / 2 + 3, vWidth / 2 - 2, 2.5, 0, Math.PI * 2);
            ctx.fill();
          } else if (v.turnIntention === 'RIGHT') {
            // Blink right lights (bottom side)
            ctx.beginPath();
            ctx.arc(vLength / 2 - 3, -vWidth / 2 + 2, 2.5, 0, Math.PI * 2);
            ctx.arc(-vLength / 2 + 3, -vWidth / 2 + 2, 2.5, 0, Math.PI * 2);
            ctx.fill();
          }
          ctx.restore();
        }

        // MiniBus Details
        if (v.type === 'MINIBUS') {
          ctx.fillStyle = '#475569';
          ctx.fillRect(-vLength / 2 + 5, -2, 4, 4); // bus windows separator
          ctx.fillRect(5, -2, 4, 4);
        }

        ctx.restore();
      });

      // 11. Draw Traffic Lights
      const drawTrafficLightObj = (x: number, y: number, state: LightState, direction: string) => {
        ctx.save();
        ctx.translate(x, y);

        // Rotate housing to point towards incoming flow
        if (direction === "EST") ctx.rotate(0);
        else if (direction === "NORD") ctx.rotate(Math.PI / 2);
        else if (direction === "OUEST") ctx.rotate(Math.PI);
        else if (direction === "SUD") ctx.rotate(Math.PI * 1.5);

        // Draw Pole
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -15);
        ctx.stroke();

        // Draw Housing (Box)
        ctx.fillStyle = colors.housing;
        ctx.beginPath();
        ctx.roundRect(-10, -45, 20, 45, 4);
        ctx.fill();
        ctx.strokeStyle = colors.curb;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Draw Bulbs (Red, Orange, Green)
        const redColor = state === "ROUGE" ? colors.redLight : colors.redLightDim;
        const orangeColor = state === "ORANGE" ? colors.orangeLight : colors.orangeLightDim;
        const greenColor = state === "VERT" ? colors.greenLight : colors.greenLightDim;

        // Draw bulbs
        ctx.fillStyle = redColor;
        ctx.beginPath(); ctx.arc(0, -36, 5, 0, Math.PI * 2); ctx.fill();
        if (state === "ROUGE" && isNight) {
          ctx.save(); ctx.shadowColor = colors.redLight; ctx.shadowBlur = 10; ctx.beginPath(); ctx.arc(0, -36, 5, 0, Math.PI * 2); ctx.fill(); ctx.restore();
        }

        ctx.fillStyle = orangeColor;
        ctx.beginPath(); ctx.arc(0, -22, 5, 0, Math.PI * 2); ctx.fill();
        if (state === "ORANGE" && isNight) {
          ctx.save(); ctx.shadowColor = colors.orangeLight; ctx.shadowBlur = 10; ctx.beginPath(); ctx.arc(0, -22, 5, 0, Math.PI * 2); ctx.fill(); ctx.restore();
        }

        ctx.fillStyle = greenColor;
        ctx.beginPath(); ctx.arc(0, -8, 5, 0, Math.PI * 2); ctx.fill();
        if (state === "VERT" && isNight) {
          ctx.save(); ctx.shadowColor = colors.greenLight; ctx.shadowBlur = 10; ctx.beginPath(); ctx.arc(0, -8, 5, 0, Math.PI * 2); ctx.fill(); ctx.restore();
        }

        ctx.restore();
      };

      // Positions of traffic lights matching stop lines
      drawTrafficLightObj(-135, -85, engine.lights.EST.state, "EST");
      drawTrafficLightObj(135, 85, engine.lights.OUEST.state, "OUEST");
      drawTrafficLightObj(85, -135, engine.lights.NORD.state, "NORD");
      drawTrafficLightObj(-85, 135, engine.lights.SUD.state, "SUD");

      // 12. Draw Pedestrian Sign Diamonds
      const drawDiamondSign = (x: number, y: number) => {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(Math.PI / 4); // 45 degrees
        ctx.fillStyle = '#eab308'; // Amber yellow
        ctx.fillRect(-6, -6, 12, 12);
        ctx.restore();

        ctx.fillStyle = '#000000';
        ctx.beginPath();
        ctx.arc(x, y + 2, 2, 0, Math.PI * 2);
        ctx.fill();
      };

      drawDiamondSign(-90, 90);
      drawDiamondSign(90, 90);
      drawDiamondSign(-90, -90);
      drawDiamondSign(90, -90);

      // Restore original context state
      ctx.restore();

      // Request next frame
      try {
        engine.tick();
      } catch (err: any) {
        console.error("Simulation crash intercepted:", err);
        fetch("http://localhost:8000/api/logs", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
            type_action: "SYSTEM_ERROR",
            action: `CRASH: ${err.message} | Stack: ${err.stack}`,
            etat_feu: engine.currentPhase,
            scenario: engine.getScenarioName(),
            id_voiture: "N/A",
            position_x: "N/A",
            position_y: "N/A",
            vitesse: "N/A"
          })
        }).catch(e => console.error("Failed to send crash log:", e));
        return; // Stop animation loop to prevent infinite crash loops
      }
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [engine]);

  return (
    <div className="relative border border-slate-700 rounded-xl overflow-hidden bg-slate-900 shadow-xl flex items-center justify-center p-2">
      <canvas
        ref={canvasRef}
        width={900}
        height={700}
        className="w-full max-w-[900px] aspect-[9/7] bg-emerald-900 rounded-lg shadow-inner"
      />
    </div>
  );
};
