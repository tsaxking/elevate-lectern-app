import { type SystemState } from "$lib/types";
import { Color } from "$lib/colors/color";
import { Gradient } from "$lib/colors/gradient";
import { Container } from "$lib/canvas/container";
import { Polygon } from "$lib/canvas/polygon";

const blue = new Color(0, 200, 255);
const green = new Color(57, 255, 20);
const yellow = new Color(255, 255, 0);
const red = new Color(255, 72, 82);

const fadeSize = .1; // 5% of the total size

const buildColorScheme = (tick: number) => {
    let color: Color;
    switch (true) {
        case tick < 0.35:
            color = blue.clone();
            break;
        case tick < 0.5:
            color = blue.linearFade(green, 10).at((tick - 0.5) / fadeSize) || green.clone();
            break;
        case tick < 0.55:
            color = green.clone();
            break;
        case tick < 0.6:
            color = green.linearFade(yellow, 10).at((tick - 0.7) / fadeSize) || yellow.clone();
            break;
        case tick < 0.8:
            color = yellow.clone();
            break;
        case tick < 0.85:
            color = yellow.linearFade(red, 10).at((tick - 0.9) / fadeSize) || red.clone();
            break;
        default:
            color = red.clone();
            break;
    }

    if (!color) {
        console.log('No color found for tick', tick);
    }

    return {
        color, tick
    }
};

export class MotorGradient extends Container {
    // private readonly gradient: Gradient;

    constructor(private state: SystemState, private frames: number) {
        super();
        const size = 1 / frames * 2;
        // const size = 0.05;

        this.children = [
        ...Array.from({ length: frames - 1 }, (_, i) => i / frames)
        .map(buildColorScheme)
        .map((color) => ({ 
            color, 
            drawable: new Polygon([
                [0.5 - color.tick / 2, 0],
                [0.5 - size - color.tick / 2, 0],
                [0.5 - size - color.tick / 2, 1],
                [0.5 - color.tick / 2, 1]
        ])})).reverse(),
        ...Array.from({ length: frames - 1 }, (_, i) => i / frames)
            .map(buildColorScheme)
            .map((color) => ({ 
                color, 
                drawable: new Polygon([
                    [0.5 + color.tick / 2, 0],
                    [0.5 + size + color.tick / 2, 0],
                    [0.5 + size + color.tick / 2, 1],
                    [0.5 + color.tick / 2, 1]
            ])})),

        ]
            .map(({ color, drawable }) => {
                drawable.fill = {
                    color: color.color.toString(),
                }
                drawable.properties.shadowBlur = 10;
                drawable.properties.shadowColor = color.color.toString();
                // drawable.draw = (ctx) => {
                //     if (Math.abs(this.state.system.motor_speed) > color.tick) {
                //         console.log('Drawing motor gradient', color.tick);
                //         super.draw(ctx);
                //     }
                // }
                return drawable;
            });

    }
    setState(state: SystemState) {
        this.state = state;
    }

    draw(ctx: CanvasRenderingContext2D) {
        this.filter((d, i, a) => {
            if (!d) return false;  // Exclude any data that might be falsy

            const motor_speed = this.state.system.motor_speed;
        
            // Calculate the middle index of the array
            const middleIndex = Math.floor(a.length / 2);
        
            if (motor_speed > 0) {
                // Show points from the middle to the right, based on motor_speed
                return i >= middleIndex && i < middleIndex + (motor_speed * middleIndex);
            } else if (motor_speed < 0) {
                // Show points from the middle to the left, based on motor_speed
                return i <= middleIndex && i > middleIndex + (motor_speed * middleIndex);
            } else {
                // If motor_speed is 0, return no points or all points (based on your preference)
                return false;  // Or `return true;` if you want to display all points when motor_speed is 0
            }
        });
        super.draw(ctx);
    }
}