import { type Point2D } from '../calculations/linear-algebra/point.js';
import { Polygon } from './polygon';

export class Border extends Polygon {
    isIn(point: Point2D) {
        return !super.isIn(point);
    }

    draw(ctx: CanvasRenderingContext2D) {
        const region = new Path2D();

        const points = this.points.map(p => this.reflect(p));

        region.moveTo(
            points[0][0] * ctx.canvas.width,
            points[0][1] * ctx.canvas.height
        );

        for (let i = 1; i < this.points.length; i++) {
            region.lineTo(
                points[i][0] * ctx.canvas.width,
                points[i][1] * ctx.canvas.height
            );
        }
        region.closePath();

        region.moveTo(0, 0);
        region.lineTo(ctx.canvas.width, 0);
        region.lineTo(ctx.canvas.width, ctx.canvas.height);
        region.lineTo(0, ctx.canvas.height);
        region.closePath();

        // fill the area between the polygon and the canvas edges
        if (this.properties?.fill?.color) {
            ctx.fillStyle = this.properties.fill.color;
        }
        if (this.properties.fill) ctx.fill(region, 'evenodd');
    }
}
