// app/api/get_poi/route.js
import { get_poi } from "@/lib/data";
import { NextResponse } from "next/server";

export async function GET(request) {
    const { searchParams } = new URL(request.url);
    const poiId = searchParams.get("poi_id");

    if (!poiId) {
        return NextResponse.json({ error: "POI ID is required" }, { status: 400 });
    }

    try {
        const poiData = await get_poi(poiId);
        return NextResponse.json(poiData);
    } catch (error) {
        console.error("Error fetching POI:", error);
        return NextResponse.json({ error: "Failed to fetch POI" }, { status: 500 });
    }
}
