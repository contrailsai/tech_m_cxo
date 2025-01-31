// app/api/get_all_pois/route.js
import { get_all_pois } from "@/lib/data";
import { NextResponse } from "next/server";

export async function GET() {
    try {
        const pois = await get_all_pois();
        return NextResponse.json(pois);
    } catch (error) {
        console.error("Error fetching POIs:", error);
        return NextResponse.json({ error: "Failed to fetch POIs" }, { status: 500 });
    }
}
